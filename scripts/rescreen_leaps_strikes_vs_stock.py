#!/usr/bin/env python3
"""
Re-screen liquid LEAPS call strikes against buying stock with the same capital.

The goal is not to find the "best" option in absolute terms. The goal is to
identify which strikes are the strongest candidates if we care about resale
value before expiration relative to same-capital stock exposure.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


REFERENCE_SPOTS = {
    "MP": 63.013,
    "MU": 401.10,
    "VRT": 243.00,
}

RISK_FREE_RATE = 0.04
DIVIDEND_YIELD = 0.0

SCENARIOS = [
    {
        "name": "stock_up_10_iv_flat_90d",
        "days_forward": 90,
        "spot_change_pct": 0.10,
        "iv_change": 0.00,
        "stock_like": True,
    },
    {
        "name": "stock_up_10_iv_up_5pts_90d",
        "days_forward": 90,
        "spot_change_pct": 0.10,
        "iv_change": 0.05,
        "stock_like": True,
    },
    {
        "name": "stock_flat_iv_up_10pts_90d",
        "days_forward": 90,
        "spot_change_pct": 0.00,
        "iv_change": 0.10,
        "stock_like": False,
    },
    {
        "name": "stock_up_20_iv_flat_180d",
        "days_forward": 180,
        "spot_change_pct": 0.20,
        "iv_change": 0.00,
        "stock_like": True,
    },
]

DOWNSIDE_SCENARIOS = [
    {
        "name": "delay_theta_drag_180d",
        "days_forward": 180,
        "spot_change_pct": 0.00,
        "iv_change": -0.05,
    },
    {
        "name": "thesis_failure_180d",
        "days_forward": 180,
        "spot_change_pct": -0.15,
        "iv_change": -0.10,
    },
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call_price(spot: float, strike: float, time_years: float, volatility: float) -> float:
    if time_years <= 0:
        return max(spot - strike, 0.0)
    if volatility <= 0:
        return max(
            spot * math.exp(-DIVIDEND_YIELD * time_years)
            - strike * math.exp(-RISK_FREE_RATE * time_years),
            0.0,
        )
    vol_sqrt_t = volatility * math.sqrt(time_years)
    d1 = (
        math.log(spot / strike)
        + (RISK_FREE_RATE - DIVIDEND_YIELD + 0.5 * volatility * volatility) * time_years
    ) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return (
        spot * math.exp(-DIVIDEND_YIELD * time_years) * _norm_cdf(d1)
        - strike * math.exp(-RISK_FREE_RATE * time_years) * _norm_cdf(d2)
    )


def _rel_spread(bid: float, ask: float) -> float | None:
    mid = (bid + ask) / 2
    if mid <= 0:
        return None
    return (ask - bid) / mid


def _evaluate_contract(
    symbol: str,
    contract: Dict[str, Any],
    captured_at: datetime,
) -> Dict[str, Any]:
    spot = REFERENCE_SPOTS[symbol]
    expiry = datetime.fromisoformat(contract["expiry"]).replace(tzinfo=timezone.utc)
    bid = float(contract["bid"])
    ask = float(contract["ask"])
    iv = float(contract["implied_volatility"])
    strike = float(contract["strike"])
    mid = (bid + ask) / 2
    cost = mid * 100.0

    bullish_excess = []
    downside_gap = []
    for scenario in SCENARIOS:
        scenario_date = captured_at + timedelta(days=scenario["days_forward"])
        time_remaining = max((expiry - scenario_date).days / 365.0, 0.0)
        scenario_spot = spot * (1.0 + scenario["spot_change_pct"])
        scenario_iv = max(iv + scenario["iv_change"], 0.01)
        option_price = _bs_call_price(scenario_spot, strike, time_remaining, scenario_iv)
        option_pnl = (option_price - mid) * 100.0
        stock_pnl = cost * scenario["spot_change_pct"]
        if not scenario["stock_like"]:
            stock_pnl = 0.0
        bullish_excess.append(option_pnl - stock_pnl)

    for scenario in DOWNSIDE_SCENARIOS:
        scenario_date = captured_at + timedelta(days=scenario["days_forward"])
        time_remaining = max((expiry - scenario_date).days / 365.0, 0.0)
        scenario_spot = spot * (1.0 + scenario["spot_change_pct"])
        scenario_iv = max(iv + scenario["iv_change"], 0.01)
        option_price = _bs_call_price(scenario_spot, strike, time_remaining, scenario_iv)
        option_pnl = (option_price - mid) * 100.0
        stock_pnl = cost * scenario["spot_change_pct"]
        downside_gap.append(option_pnl - stock_pnl)

    rel_spread = _rel_spread(bid, ask)
    return {
        "symbol": symbol,
        "option_symbol": contract["option_symbol"],
        "strike": strike,
        "mid": round(mid, 3),
        "open_interest": contract.get("open_interest"),
        "implied_volatility": iv,
        "relative_spread": round(rel_spread, 4) if rel_spread is not None else None,
        "bullish_excess_vs_stock_mean": round(sum(bullish_excess) / len(bullish_excess), 2),
        "best_bullish_excess_vs_stock": round(max(bullish_excess), 2),
        "worst_downside_gap_vs_stock": round(min(downside_gap), 2),
    }


def _screen_symbol(symbol: str, snapshot_path: Path) -> List[Dict[str, Any]]:
    payload = _load_json(snapshot_path)
    captured_at = datetime.fromisoformat(payload["capture_meta"]["captured_at"].replace("Z", "+00:00"))
    contracts = payload["expiries"][0]["contracts"]
    eligible = []
    for contract in contracts:
        if contract.get("right") != "call":
            continue
        if not isinstance(contract.get("bid"), (int, float)) or not isinstance(contract.get("ask"), (int, float)):
            continue
        if contract["ask"] <= 0:
            continue
        if (contract.get("open_interest") or 0) < 100:
            continue
        rel_spread = _rel_spread(contract["bid"], contract["ask"])
        if rel_spread is None or rel_spread > 0.09:
            continue
        iv = contract.get("implied_volatility")
        if not isinstance(iv, (int, float)) or iv <= 0:
            continue
        eligible.append(_evaluate_contract(symbol, contract, captured_at))

    return sorted(
        eligible,
        key=lambda row: (
            -row["bullish_excess_vs_stock_mean"],
            row["relative_spread"],
            -(row["open_interest"] or 0),
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Rescreen LEAPS strikes versus same-capital stock")
    parser.add_argument("--output-json", required=True, help="Path to write output JSON")
    args = parser.parse_args()

    snapshot_paths = {
        "MP": Path("research/options-data/2026-03-15/MP-chain-yahoo-2027-01-15.json"),
        "MU": Path("research/options-data/2026-03-15/MU-chain-yahoo-2027-01-15.json"),
        "VRT": Path("research/options-data/2026-03-15/VRT-chain-yahoo-2027-01-15.json"),
    }

    output = {
        "method": "same-capital option-vs-stock rescreen using rough pre-expiration scenario estimates",
        "symbols": {
            symbol: _screen_symbol(symbol, path)[:8]
            for symbol, path in snapshot_paths.items()
        },
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
