#!/usr/bin/env python3
"""
Refresh a LEAPS watchlist from normalized options-chain snapshots.

This script appends one observation per entry when the target contract is found
in the configured snapshot file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mid(bid: Any, ask: Any) -> float | None:
    if not isinstance(bid, (int, float)) or not isinstance(ask, (int, float)):
        return None
    return round((bid + ask) / 2, 3)


def _rel_spread(bid: Any, ask: Any) -> float | None:
    midpoint = _mid(bid, ask)
    if midpoint is None or midpoint <= 0:
        return None
    return round((ask - bid) / midpoint, 4)


def _extract_observation(entry: Dict[str, Any], snapshot_payload: Dict[str, Any]) -> Dict[str, Any] | None:
    option_symbol = entry["option_symbol"]
    expiry_blocks = snapshot_payload.get("expiries", [])
    for expiry_block in expiry_blocks:
        for contract in expiry_block.get("contracts", []):
            if contract.get("option_symbol") != option_symbol:
                continue
            bid = contract.get("bid")
            ask = contract.get("ask")
            return {
                "captured_at": snapshot_payload["capture_meta"].get("captured_at"),
                "snapshot_path": entry["snapshot_path"],
                "option_symbol": option_symbol,
                "bid": bid,
                "ask": ask,
                "mid": _mid(bid, ask),
                "open_interest": contract.get("open_interest"),
                "volume": contract.get("volume"),
                "implied_volatility": contract.get("implied_volatility"),
                "relative_spread": _rel_spread(bid, ask),
            }
    return None


def _append_observation(entry: Dict[str, Any], observation: Dict[str, Any]) -> None:
    history: List[Dict[str, Any]] = entry.setdefault("tracking_history", [])
    key = (observation["captured_at"], observation["option_symbol"])
    seen = {(row.get("captured_at"), row.get("option_symbol")) for row in history}
    if key not in seen:
        history.append(observation)
    entry["latest_observation"] = observation


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh LEAPS watchlist observations")
    parser.add_argument("watchlist_json", help="Path to watchlist JSON")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write updates back to the watchlist file instead of printing",
    )
    args = parser.parse_args()

    path = Path(args.watchlist_json)
    watchlist = _load_json(path)

    for entry in watchlist.get("entries", []):
        snapshot_path = Path(entry["snapshot_path"])
        payload = _load_json(snapshot_path)
        observation = _extract_observation(entry, payload)
        if observation is not None:
            _append_observation(entry, observation)

    output = json.dumps(watchlist, indent=2) + "\n"
    if args.write:
        path.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
