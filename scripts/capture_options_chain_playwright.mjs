#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch (error) {
  console.error(
    "Playwright is not installed. Add it with `npm install --save-dev playwright` before running this script.",
  );
  process.exit(1);
}

function parseArgs(argv) {
  const args = {
    headless: false,
    outDir: "research/options-data/raw",
    provider: "public-page-playwright",
    maxRows: 500,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith("--")) {
      continue;
    }
    const key = value.slice(2);
    if (key === "headless") {
      args.headless = true;
      continue;
    }
    const next = argv[index + 1];
    if (next == null || next.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }
    args[key] = next;
    index += 1;
  }

  if (!args.url) {
    throw new Error("Missing required --url");
  }
  if (!args.underlying) {
    throw new Error("Missing required --underlying");
  }

  args.maxRows = Number(args.maxRows) || 500;
  return args;
}

function slugify(value) {
  return String(value)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function toCsv(headers, rows) {
  const escapeCell = (value) => {
    const text = value == null ? "" : String(value);
    if (/[",\n]/.test(text)) {
      return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  };

  const headerLine = headers.map(escapeCell).join(",");
  const rowLines = rows.map((row) => headers.map((header) => escapeCell(row[header])).join(","));
  return [headerLine, ...rowLines].join("\n") + "\n";
}

function pickBestTable(tables) {
  return [...tables].sort((left, right) => right.score - left.score || right.row_count - left.row_count)[0];
}

const args = parseArgs(process.argv.slice(2));
const browser = await chromium.launch({
  headless: args.headless,
  chromiumSandbox: false,
  args: ["--disable-setuid-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 } });

if (args.waitForSelector) {
  await page.goto(args.url, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(args.waitForSelector, { timeout: 30000 });
} else {
  await page.goto(args.url, { waitUntil: "domcontentloaded" });
}

const rl = readline.createInterface({ input, output });
output.write(
  [
    "",
    `Opened ${args.url}`,
    "Prepare the page manually in the browser:",
    "- select the expiry you want",
    "- make the target options table visible",
    "- then press Enter here to capture the visible tables",
    "",
  ].join("\n"),
);
await rl.question("> ");
await rl.close();

const snapshot = await page.evaluate(
  ({ explicitSelector, maxRows }) => {
    const normalizeHeader = (value) =>
      value
        .trim()
        .toLowerCase()
        .replace(/\s+/g, " ")
        .replace(/[^a-z0-9 %/()-]+/g, "");

    const headerKeywords = new Map([
      ["strike", 4],
      ["bid", 3],
      ["ask", 3],
      ["last", 2],
      ["mark", 2],
      ["volume", 2],
      ["vol", 2],
      ["open interest", 3],
      ["oi", 3],
      ["iv", 2],
      ["implied volatility", 2],
      ["delta", 1],
      ["gamma", 1],
      ["theta", 1],
      ["vega", 1],
      ["call", 1],
      ["put", 1],
    ]);

    const visible = (element) => {
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return (
        style.visibility !== "hidden" &&
        style.display !== "none" &&
        rect.width > 0 &&
        rect.height > 0
      );
    };

    const collectContext = (table) => {
      const parts = [];
      const caption = table.querySelector("caption");
      if (caption && caption.textContent?.trim()) {
        parts.push(caption.textContent.trim());
      }

      let node = table.previousElementSibling;
      let hops = 0;
      while (node && hops < 4) {
        if (/^(H1|H2|H3|H4|H5|H6|DIV|SPAN|P)$/i.test(node.tagName)) {
          const text = node.textContent?.trim();
          if (text) {
            parts.push(text);
            break;
          }
        }
        node = node.previousElementSibling;
        hops += 1;
      }
      return parts.join(" | ");
    };

    const scoreTable = (headers, rowCount, contextText) => {
      let score = 0;
      for (const header of headers) {
        const normalized = normalizeHeader(header);
        for (const [keyword, weight] of headerKeywords.entries()) {
          if (normalized.includes(keyword)) {
            score += weight;
          }
        }
      }
      const context = normalizeHeader(contextText);
      if (context.includes("call")) score += 2;
      if (context.includes("put")) score += 2;
      if (context.includes("option")) score += 2;
      if (context.includes("expiry")) score += 1;
      score += Math.min(rowCount, 100) / 25;
      return Number(score.toFixed(1));
    };

    const tables = Array.from(
      explicitSelector ? document.querySelectorAll(explicitSelector) : document.querySelectorAll("table"),
    ).filter(visible);

    return tables.map((table, index) => {
      const headerCells = Array.from(table.querySelectorAll("thead th")).filter((cell) => visible(cell));
      const fallbackHeaderRow =
        headerCells.length === 0 ? Array.from(table.querySelectorAll("tr")).find((row) => row.querySelector("th")) : null;
      const headers =
        headerCells.length > 0
          ? headerCells.map((cell) => cell.textContent?.trim() || "")
          : fallbackHeaderRow
            ? Array.from(fallbackHeaderRow.children).map((cell) => cell.textContent?.trim() || "")
            : [];

      const rowNodes = Array.from(table.querySelectorAll("tbody tr")).filter((row) => visible(row));
      const fallbackRows =
        rowNodes.length === 0
          ? Array.from(table.querySelectorAll("tr")).filter(
              (row) => visible(row) && !row.closest("thead"),
            )
          : rowNodes;
      const rows = [];
      for (const rowNode of fallbackRows) {
        const cells = Array.from(rowNode.children).filter((cell) => visible(cell));
        if (cells.length === 0) continue;
        const row = {};
        cells.slice(0, headers.length || cells.length).forEach((cell, cellIndex) => {
          const key = headers[cellIndex] || `col_${cellIndex + 1}`;
          row[key] = cell.textContent?.trim() || "";
        });
        const allValuesEmpty = Object.values(row).every((value) => value === "");
        if (!allValuesEmpty) {
          rows.push(row);
        }
        if (rows.length >= maxRows) break;
      }

      const contextText = collectContext(table);
      return {
        table_index: index,
        context_text: contextText,
        headers,
        row_count: rows.length,
        score: scoreTable(headers, rows.length, contextText),
        rows,
      };
    });
  },
  {
    explicitSelector: args.tableSelector || null,
    maxRows: args.maxRows,
  },
);

await browser.close();

if (snapshot.length === 0) {
  console.error("No visible tables found to capture.");
  process.exit(2);
}

const bestTable = pickBestTable(snapshot);
const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const baseDir = path.resolve(args.outDir, args.underlying.toUpperCase(), stamp);
await fs.mkdir(baseDir, { recursive: true });

const captureSummary = {
  capture_meta: {
    provider: args.provider,
    captured_at: new Date().toISOString(),
    underlying: args.underlying.toUpperCase(),
    capture_mode: "user_mediated_playwright",
    source_page: args.url,
    selected_table_index: bestTable.table_index,
    selected_table_context: bestTable.context_text,
    table_selector: args.tableSelector || null,
    notes: [
      "Visible tables were captured after manual page preparation.",
      "Review the raw CSV before normalization.",
    ],
  },
  tables: snapshot,
};

await fs.writeFile(
  path.join(baseDir, "capture-summary.json"),
  JSON.stringify(captureSummary, null, 2) + "\n",
  "utf8",
);

await fs.writeFile(
  path.join(baseDir, "best-table.csv"),
  toCsv(bestTable.headers, bestTable.rows),
  "utf8",
);

output.write(
  [
    "",
    `Captured ${snapshot.length} visible table(s).`,
    `Best table: #${bestTable.table_index} (${bestTable.context_text || "no context"})`,
    `Rows: ${bestTable.row_count}, score: ${bestTable.score}`,
    `Artifacts written to: ${baseDir}`,
    "Next step: inspect best-table.csv, then normalize it with scripts/normalize_options_chain_snapshot.py.",
    "",
  ].join("\n"),
);
