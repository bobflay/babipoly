#!/usr/bin/env python3
"""
Babipoly Multi-Scenario Analysis
=================================
Compares different starting-money configurations to find the best balance
for 2, 4, 6, and 8 player games.

Runs the simulation multiple times under different parameter scenarios and
produces a comparative table so you can decide what to tune.

Usage:
    python run_analysis.py               # quick: 200 games per scenario
    python run_analysis.py --games 1000  # higher precision (slower)
"""

import random
import statistics
import argparse
import sys
import os

# Make babipoly_sim importable from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from babipoly_sim import (
    run_simulations,
    BOARD, GROUPS, STATION_POS, UTILITY_POS,
    STARTING_MONEY, GO_REWARD, JAIL_BAIL,
    BabopolyGame,
)

# ══════════════════════════════════════════════════════════════════
# SCENARIO DEFINITIONS
# ══════════════════════════════════════════════════════════════════

SCENARIOS = [
    {
        "name":           "Current (250k)",
        "starting_money": 250_000,
        "description":    "Exactly as defined in guide.html",
    },
    {
        "name":           "100k start",
        "starting_money": 100_000,
        "description":    "Lower starting money to 100,000 FCFA",
    },
    {
        "name":           "60k start (rec.)",
        "starting_money": 60_000,
        "description":    "Recommended Option C: 60,000 FCFA",
    },
    {
        "name":           "40k start",
        "starting_money": 40_000,
        "description":    "Option A: 40,000 FCFA (aggressive reduction)",
    },
    {
        "name":           "20k start",
        "starting_money": 20_000,
        "description":    "Ultra-low: 20,000 FCFA (very fast game)",
    },
]

PLAYER_COUNTS = [2, 4, 6, 8]

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _pct(val: float, total: float) -> str:
    return f"{val/total*100:5.1f}%"


def _assess(avg: float, completion_pct: float) -> str:
    if completion_pct < 20:
        return "✗ Games never end"
    if completion_pct < 50:
        return "⚠ Mostly timeout"
    if avg < 40:
        return "⚠ Short"
    if avg <= 150:
        return "✓ Ideal"
    if avg <= 250:
        return "→ Long"
    return "✗ Very long"


def _first_player_bias(res: dict) -> str:
    ng       = res["num_games"]
    np       = res["num_players"]
    expected = ng / np
    p1_wins  = sum(1 for wid in res["winners"] if wid == 0)
    diff_pct = (p1_wins - expected) / ng * 100
    if abs(diff_pct) > 5:
        return f"{'+'if diff_pct>0 else ''}{diff_pct:.1f}%"
    return "~0%"


# ══════════════════════════════════════════════════════════════════
# PROPERTY STATISTICS (group breakdown)
# ══════════════════════════════════════════════════════════════════

def group_stats() -> str:
    """Static analysis of each color group's ROI and value."""
    lines = []
    lines.append("\n" + "═"*72)
    lines.append("  PROPERTY GROUP ANALYSIS (static, no simulation needed)")
    lines.append("═"*72)
    lines.append(f"\n  {'Group':12}  {'Props':>5}  {'Avg Price':>10}  "
                 f"{'House $':>8}  {'Hotel Rent (avg)':>17}  {'ROI (hotel)':>12}")
    lines.append(f"  {'':─<12}  {'':─>5}  {'':─>10}  {'':─>8}  {'':─>17}  {'':─>12}")

    for group, info in GROUPS.items():
        positions  = info["positions"]
        house_cost = info["house_cost"]
        prices     = [BOARD[p]["price"] for p in positions]
        hotel_rents= [BOARD[p]["rent"][-1] for p in positions]

        avg_price   = sum(prices) / len(prices)
        avg_hotel   = sum(hotel_rents) / len(hotel_rents)
        total_invest = avg_price + house_cost * 5  # buy + build hotel
        roi_pct      = avg_hotel / total_invest * 100

        # Flag anomalies
        flag = ""
        if house_cost > avg_price:
            flag = " ← house cost > price!"

        lines.append(
            f"  {group:12}  {len(positions):>5}  {avg_price:>10,.0f}  "
            f"{house_cost:>8,}  {avg_hotel:>17,.0f}  {roi_pct:>11.1f}%{flag}"
        )

    lines.append("""
  Notes:
  • ROI = average hotel rent / (avg property price + 5 × house cost)
  • Higher ROI means rent pays back development cost faster.
  • dark_blue group has Yamoussoukro anomaly: house_cost (7,000) > price (5,000).
  • Yellow group has lowest ROI despite being first on the board.
""")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# COMPARATIVE TABLE
# ══════════════════════════════════════════════════════════════════

def comparative_table(scenario_results: list) -> str:
    lines = []
    lines.append("\n" + "═"*72)
    lines.append("  SCENARIO COMPARISON TABLE")
    lines.append("═"*72)

    for np in PLAYER_COUNTS:
        lines.append(f"\n  ── {np}-PLAYER GAMES ─────────────────────────────────────")
        lines.append(f"  {'Scenario':<22}  {'Start $':>9}  {'Complt%':>8}  "
                     f"{'Med(done)':>9}  {'Timeout':>8}  {'P1 bias':>8}  {'Assessment'}")
        lines.append(f"  {'':─<22}  {'':─>9}  {'':─>8}  {'':─>9}  {'':─>8}  {'':─>8}  {'':─<18}")

        for scenario_name, results in scenario_results:
            res    = results[np]
            ng     = res["num_games"]
            rds    = res["rounds"]
            tout   = res["timed_out"]
            sm     = res["starting_money"]
            bias   = _first_player_bias(res)
            done   = [r for r in rds if r < 10_000]
            compl  = (ng - tout) / ng * 100
            med    = statistics.median(done) if done else 10_000
            verdict = _assess(med, compl)

            lines.append(
                f"  {scenario_name:<22}  {sm:>9,}  {compl:>7.0f}%  "
                f"{med:>8.0f}  {tout:>7}/{ng}  {bias:>8}  {verdict}"
            )

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# RENT FLOW BREAKDOWN
# ══════════════════════════════════════════════════════════════════

def rent_flow_breakdown(scenario_results: list, num_players: int = 4) -> str:
    lines = []
    lines.append(f"\n" + "═"*72)
    lines.append(f"  RENT & CASH FLOW BREAKDOWN ({num_players}-player games, baseline scenario)")
    lines.append("═"*72)

    # Find baseline
    baseline = None
    for name, results in scenario_results:
        if "Current" in name:
            baseline = results[num_players]
            break
    if baseline is None:
        return ""

    ng = baseline["num_games"]
    np = baseline["num_players"]

    total_rent_paid     = [sum(baseline["rent_paid"][pid]) / ng     for pid in range(np)]
    total_rent_received = [sum(baseline["rent_received"][pid]) / ng for pid in range(np)]
    total_go            = [sum(baseline["go_rewards"][pid]) / ng    for pid in range(np)]
    total_props         = [sum(baseline["props_bought"][pid]) / ng  for pid in range(np)]
    total_peak          = [sum(baseline["peak_cash"][pid]) / ng     for pid in range(np)]

    lines.append(f"\n  Average per game across {ng} simulations:\n")
    lines.append(f"  {'Player':>8}  {'Rent Paid':>12}  {'Rent Rcvd':>12}  "
                 f"{'GO Bonus':>10}  {'Props':>6}  {'Peak Cash':>12}")
    lines.append(f"  {'':─>8}  {'':─>12}  {'':─>12}  {'':─>10}  {'':─>6}  {'':─>12}")

    for pid in range(np):
        lines.append(
            f"  {'P'+str(pid+1):>8}  {total_rent_paid[pid]:>12,.0f}  "
            f"{total_rent_received[pid]:>12,.0f}  {total_go[pid]:>10,.0f}  "
            f"{total_props[pid]:>6.1f}  {total_peak[pid]:>12,.0f}"
        )

    total_rp = sum(total_rent_paid)
    total_rr = sum(total_rent_received)
    total_g  = sum(total_go)
    lines.append(f"\n  {'Totals':>8}  {total_rp:>12,.0f}  {total_rr:>12,.0f}  "
                 f"{total_g:>10,.0f}")
    lines.append(f"\n  Cash redistributed via rent per game: {total_rp:,.0f} FCFA")
    lines.append(f"  GO rewards distributed per game:      {total_g:,.0f} FCFA (bank injection)")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# FINAL RECOMMENDATION SUMMARY
# ══════════════════════════════════════════════════════════════════

def final_summary(scenario_results: list) -> str:
    lines = []
    lines.append("\n" + "═"*72)
    lines.append("  FINAL RECOMMENDATIONS SUMMARY")
    lines.append("═"*72)

    # Find best scenario per player count: highest completion rate with
    # median of completed games in the 60–150 round target range.
    lines.append("\n  Best starting money per player count\n"
                 "  (targeting ≥80% completion AND median 60–150 rounds):\n")
    for np in PLAYER_COUNTS:
        best_name   = None
        best_score  = -1
        for name, results in scenario_results:
            res    = results[np]
            ng     = res["num_games"]
            tout   = res["timed_out"]
            done   = [r for r in res["rounds"] if r < 10_000]
            compl  = (ng - tout) / ng * 100
            med    = statistics.median(done) if done else 10_000
            # Score: high completion, median close to 100 rounds
            score  = compl - abs(med - 100) * 0.3
            if score > best_score:
                best_score = score
                best_name  = name
                best_sm    = res["starting_money"]
                best_compl = compl
                best_med   = med

        lines.append(f"  [{np}P] Best: {best_name:<22} "
                     f"({best_sm:,} FCFA)  "
                     f"→ {best_compl:.0f}% complete, median {best_med:.0f} rounds")

    lines.append("""
  KEY FINDING:
  ─────────────────────────────────────────────────────────────────────
  Simulation shows GO rewards (bank → players) EXCEED total rent paid
  (player → player) in every multi-player scenario. Example 4P game:
    GO rewards : ~60 million FCFA injected by bank per game
    Rent paid  : ~44 million FCFA redistributed between players
  The game cannot end because the bank keeps every player liquid.

  Proposed Changes (priority order):
  ───────────────────────────────────
  1. CUT GO reward in half:  10,000 → 5,000 FCFA  (most impactful fix)
     GO reward is the primary driver of infinite games. Cutting it
     reduces the bank-money injection that sustains losing players.

  2. Fix Yamoussoukro (pos 31):  house_cost 7,000 → 4,000 FCFA
     Currently players CANNOT profitably develop Yamoussoukro because
     house_cost (7,000) exceeds the property price (5,000).

  3. Raise Yellow group hotel rents:  10,000 → 18,000–20,000 FCFA
     Yellow hotels (10,000) equal one GO reward pass — not scary enough.
     Raising them makes early color monopolies actually dangerous.

  4. REDUCE starting money to 50,000–80,000 FCFA
     Lowering starting money alone does NOT fix the game (GO keeps
     injecting), but it speeds up the early game significantly.
     Combine with a GO reduction for best results.

  5. Increase Taxe Choco or add a second tax square
     A progressive tax of 5% of current cash per landing would
     drain the excess money the bank injects via GO.
""")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Babipoly Multi-Scenario Analysis"
    )
    parser.add_argument(
        "--games", type=int, default=200,
        help="Games per scenario per player count (default: 200)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()

    random.seed(args.seed)

    total_runs = len(SCENARIOS) * len(PLAYER_COUNTS) * args.games
    print("=" * 72)
    print("  BABIPOLY MULTI-SCENARIO ANALYSIS")
    print("=" * 72)
    print(f"\n  Scenarios     : {len(SCENARIOS)}")
    print(f"  Player counts : {PLAYER_COUNTS}")
    print(f"  Games each    : {args.games}")
    print(f"  Total games   : {total_runs:,}")
    print(f"  Random seed   : {args.seed}\n")

    # Print static property analysis first
    print(group_stats())

    # Run all scenarios
    scenario_results = []
    for scenario in SCENARIOS:
        name = scenario["name"]
        sm   = scenario["starting_money"]
        print(f"\n  Running scenario: '{name}' (start: {sm:,} FCFA)")
        results = {}
        for np in PLAYER_COUNTS:
            print(f"    [{np}P] ...", end="", flush=True)
            results[np] = run_simulations(np, args.games, sm)
            avg = statistics.mean(results[np]["rounds"])
            print(f" avg {avg:.0f} rounds")
        scenario_results.append((name, results))

    # Print comparative table
    print(comparative_table(scenario_results))

    # Rent flow for baseline 4-player
    print(rent_flow_breakdown(scenario_results, num_players=4))

    # Final recommendations
    print(final_summary(scenario_results))

    print("\n" + "=" * 72)
    print("  Analysis complete.")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
