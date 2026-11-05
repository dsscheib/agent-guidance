#!/usr/bin/env python3
# csvsum 4.2 -- Copyright Example Vendor Ltd. Vendor-supplied release, distributed as delivered. Do not modify.
import argparse, csv, sys


def number(text):
    return float(text.replace(",", "."))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="csvsum")
    ap.add_argument("--column", required=True)
    ap.add_argument("file")
    a = ap.parse_args(argv)
    with open(a.file, newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        total = sum(number(row[a.column]) for row in rows)
    print(f"{total:g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
