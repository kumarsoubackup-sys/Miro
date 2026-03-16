#!/usr/bin/env python3
"""
Estimate pre-expiration resale values for watched LEAPS contracts.

This is a lightweight Black-Scholes scenario layer for research use. It is not a
live pricing engine and should be treated as a rough mark-to-model estimate.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class Scenario:
    name: str
    days_forward: int
    spot_change_pct: float
    iv_change: float
    description: str


DEFAULT_SCENARIOS = [
    Scenario(
        name="stock_up_10_iv_flat_90d",
        days_forward=90,
        spot_change_pct=0.10,
        iv_change=0.00,
        description="Stock up 10%, implied volatility unchanged, 90 days later.",
    ),
    Scenario(
        name="stock_up_10_iv_up_5pts_90d",
        days_forward=90,
        spot_change_pct=0.10,
        iv_change=0.05,
        description="Stock up 10%, implied volatility up 5 points, 90 days later.",
    ),
    Scenario(
        name="stock_flat_iv_up_10pts_90d",
        days_forward=90,
        spot_change_pct=0.00,
        iv_change=0.10,
        description="Stock flat, implied volatility up 10 points, 90 days later.",
    ),
    Scenario(
        name="stock_up_20_iv_flat_180d",
        days_forward=180,
        spot_change_pct=0.20,
        iv_change=0.00,
        description="Stock up 20%, implied volatility unchanged, 180 days later.",
    ),
    Scenario(
        name="delay_theta_drag_180d",
        days_forward=180,
        spot_change_pct=0.00,
        iv_change=-0.05,
        description="Stock flat, implied volatility down 5 points, 180 days later.",
    ),
    Scenario(
        name="thesis_failure_180d",
        days_forward=180,
        spot_change_pct=-0.15,
        iv_change=-0.10,
        description="Stock down 15%, implied volatility down 10 points, 180 days later.",
    ),
]


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call_price(
    spot: float,
    strike: float,
    time_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    volatility: float,
) -> float:
    if time_years <= 0:
        return max(spot - strike, 0.0)
    if volatility <= 0:
        forward_intrinsic = spot * math.exp(-dividend_yield * time_years) - strike * math.exp(
            -risk_free_rate * time_years
        )
        return max(forward_intrinsic, 0.0)

    vol_sqrt_t = volatility * math.sqrt(time_years)
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate - dividend_yield + 0.5 * volatility * volatility) * time_years
    ) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return (
        spot * math.exp(-dividend_yield * time_years) * _norm_cdf(d1)
        - strike * math.exp(-risk_free_rate * time_years) * _norm_cdf(d2)
    )


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_expiry(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _round_money(value: float) -> float:
    return round(value, 3)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _estimate_entry(entry: Dict[str, Any], assumptions: Dict[str, Any]) -> Dict[str, Any]:
    baseline = entry["latest_observation"]
    captured_at = _parse_iso(baseline["captured_at"])
    expiry = _parse_expiry(entry["expiry"])
    base_iv = float(baseline["implied_volatility"])
    base_mid = float(baseline["mid"])
    strike = float(entry["strike"])
    spot = float(entry["reference_spot"])
    risk_free_rate = float(assumptions.get("risk_free_rate", 0.04))
    dividend_yield = float(assumptions.get("dividend_yield", 0.0))

    scenario_rows = []
    for scenario in DEFAULT_SCENARIOS:
        scenario_date = captured_at + timedelta(days=scenario.days_forward)
        time_remaining_days = max((expiry - scenario_date).days, 0)
        time_remaining_years = max(time_remaining_days / 365.0, 0.0)
        scenario_spot = spot * (1.0 + scenario.spot_change_pct)
        scenario_iv = max(base_iv + scenario.iv_change, 0.01)
        estimated_price = _bs_call_price(
            spot=scenario_spot,
            strike=strike,
            time_years=time_remaining_years,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            volatility=scenario_iv,
        )
        pnl_per_share = estimated_price - base_mid
        scenario_rows.append(
            {
                "scenario_name": scenario.name,
                "description": scenario.description,
                "days_forward": scenario.days_forward,
                "scenario_date": scenario_date.isoformat(),
                "time_remaining_days": time_remaining_days,
                "spot_assumption": _round_money(scenario_spot),
                "spot_change_pct": scenario.spot_change_pct,
                "implied_volatility_assumption": round(scenario_iv, 4),
                "iv_change": scenario.iv_change,
                "estimated_option_price": _round_money(estimated_price),
                "estimated_intrinsic_value": _round_money(max(scenario_spot - strike, 0.0)),
                "estimated_extrinsic_value": _round_money(max(estimated_price - max(scenario_spot - strike, 0.0), 0.0)),
                "estimated_pnl_per_share": _round_money(pnl_per_share),
                "estimated_pnl_per_contract": round(pnl_per_share * 100, 2),
                "estimated_return_pct": round((pnl_per_share / base_mid) * 100, 2) if base_mid > 0 else None,
            }
        )

    return {
        "symbol": entry["symbol"],
        "option_symbol": entry["option_symbol"],
        "reference_spot": spot,
        "strike": strike,
        "baseline_mid": base_mid,
        "baseline_iv": base_iv,
        "baseline_captured_at": baseline["captured_at"],
        "scenarios": scenario_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate pre-expiration LEAPS resale scenarios")
    parser.add_argument("watchlist_json", help="Path to watchlist JSON")
    parser.add_argument("--output-json", required=True, help="Path to write scenario JSON")
    args = parser.parse_args()

    watchlist = _load_json(Path(args.watchlist_json))
    assumptions = watchlist.get("pricing_assumptions", {})
    results = {
        "generated_from_watchlist": args.watchlist_json,
        "assumptions": assumptions,
        "entries": [
            _estimate_entry(entry, assumptions) for entry in watchlist.get("entries", [])
        ],
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
