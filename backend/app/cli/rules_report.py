"""Prints the rules report JSON for APP_NOW.

Run: APP_NOW=2026-11-11T15:00:00Z python -m app.cli.rules_report [--out rules_report.json]
"""
import argparse
import json
from pathlib import Path

from app.core.clock import now
from app.db.session import SessionLocal
from app.services.report import rules_report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, help="also write the JSON to this file")
    args = p.parse_args()
    with SessionLocal() as db:
        out = json.dumps(rules_report(db, now()), indent=2) + "\n"
    print(out, end="")
    if args.out:
        args.out.write_text(out)


if __name__ == "__main__":
    main()
