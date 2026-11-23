#!/usr/bin/env python3
"""home_energy_estimator

A command‑line tool that reads two CSV files – one describing appliances and their power ratings, and another describing a daily usage schedule – and prints the estimated kWh consumption for each day and for the entire period.  An optional ``--confidence`` flag shows ±5 % bounds based on the assumption that each appliance’s power rating may vary by 5 %.

The module exposes a single ``main`` function that accepts an optional ``argv`` list.  It is designed to be invoked directly or via ``python -m home_energy_estimator``.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sys
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate home energy consumption from appliance power ratings and usage schedule."
    )
    parser.add_argument(
        "--appliances",
        required=True,
        type=Path,
        help="Path to CSV file with columns name,power_watts",
    )
    parser.add_argument(
        "--schedule",
        required=True,
        type=Path,
        help="Path to CSV file with columns name,day,hours",
    )
    parser.add_argument(
        "--period",
        required=True,
        type=int,
        help="Number of days to compute",
    )
    parser.add_argument(
        "--confidence",
        action="store_true",
        help="Show ±5%% confidence bounds",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# CSV reading helpers
# ---------------------------------------------------------------------------

def read_appliances(path: Path) -> dict[str, Decimal]:
    appliances: dict[str, Decimal] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            try:
                power = Decimal(row["power_watts"])
            except (ValueError, InvalidOperation):
                raise ValueError(f"Invalid power_watts for appliance '{name}'")
            if power < 0:
                raise ValueError(f"Negative power for appliance '{name}'")
            appliances[name] = power
    return appliances


def read_schedule(path: Path) -> list[tuple[str, int, Decimal]]:
    schedule: list[tuple[str, int, Decimal]] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            try:
                day = int(row["day"])
            except (ValueError, InvalidOperation):
                raise ValueError(f"Invalid day for appliance '{name}'")
            try:
                hours = Decimal(row["hours"])
            except (ValueError, InvalidOperation):
                raise ValueError(f"Invalid hours for appliance '{name}'")
            if hours < 0:
                raise ValueError(f"Negative hours for appliance '{name}'")
            schedule.append((name, day, hours))
    return schedule


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_totals(
    appliances: dict[str, Decimal],
    schedule: list[tuple[str, int, Decimal]],
    period: int,
    confidence: bool,
) -> tuple[
    dict[int, Decimal],
    dict[str, Decimal],
    Decimal,
    dict[int, tuple[Decimal, Decimal]],
    dict[str, tuple[Decimal, Decimal]],
    Decimal,
    Decimal,
]:
    per_day: dict[int, Decimal] = {day: Decimal("0") for day in range(1, period + 1)}
    per_appliance: dict[str, Decimal] = {name: Decimal("0") for name in appliances}

    for name, day, hours in schedule:
        if name not in appliances:
            raise ValueError(f"Schedule references unknown appliance '{name}'")
        if day < 1 or day > period:
            raise ValueError(f"Schedule day {day} out of period range 1-{period}")
        power = Decimal(str(appliances[name]))
        hours = Decimal(str(hours))
        kwh = power * hours / Decimal("1000")
        per_day[day] += kwh
        per_appliance[name] += kwh

    period_total = sum(per_day.values(), Decimal("0"))

    if confidence:
        per_day_bounds: dict[int, tuple[Decimal, Decimal]] = {}
        per_appliance_bounds: dict[str, tuple[Decimal, Decimal]] = {}
        for day, total in per_day.items():
            lower = total * Decimal("0.95")
            upper = total * Decimal("1.05")
            per_day_bounds[day] = (lower, upper)
        for name, total in per_appliance.items():
            lower = total * Decimal("0.95")
            upper = total * Decimal("1.05")
            per_appliance_bounds[name] = (lower, upper)
        period_lower = period_total * Decimal("0.95")
        period_upper = period_total * Decimal("1.05")
        return (
            per_day,
            per_appliance,
            period_total,
            per_day_bounds,
            per_appliance_bounds,
            period_lower,
            period_upper,
        )
    else:
        return (
            per_day,
            per_appliance,
            period_total,
            {},
            {},
            Decimal("0"),
            Decimal("0"),
        )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def format_kwh(value: Decimal) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    try:
        args = parse_args(argv)
        appliances = read_appliances(args.appliances)
        schedule = read_schedule(args.schedule)
        (
            per_day,
            per_appliance,
            period_total,
            per_day_bounds,
            per_appliance_bounds,
            period_lower,
            period_upper,
        ) = compute_totals(
            appliances, schedule, args.period, args.confidence
        )

        for day in sorted(per_day):
            line = f"Day {day}: {format_kwh(per_day[day])} kWh"
            if args.confidence:
                lower, upper = per_day_bounds[day]
                line += f" ({format_kwh(lower)}-{format_kwh(upper)})"
            print(line)

        print("\nPer appliance totals:")
        for name in sorted(per_appliance):
            line = f"  {name}: {format_kwh(per_appliance[name])} kWh"
            if args.confidence:
                lower, upper = per_appliance_bounds[name]
                line += f" ({format_kwh(lower)}-{format_kwh(upper)})"
            print(line)

        line = f"\nPeriod total: {format_kwh(period_total)} kWh"
        if args.confidence:
            line += f" ({format_kwh(period_lower)}-{format_kwh(period_upper)})"
        print(line)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
