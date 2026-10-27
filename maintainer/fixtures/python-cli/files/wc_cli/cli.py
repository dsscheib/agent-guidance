"""Count lines, words and characters in text files."""
import argparse
import sys


def count_words(text):
    return len(text.split())


def summarize(text):
    return {"lines": text.count("\n"), "words": count_words(text), "chars": len(text)}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wc-cli", description=__doc__)
    parser.add_argument("path", help="file to count, or - for standard input")
    args = parser.parse_args(argv)
    if args.path == "-":
        text = sys.stdin.read()
    else:
        with open(args.path, encoding="utf-8") as handle:
            text = handle.read()
    counts = summarize(text)
    print(f"{counts['lines']} {counts['words']} {counts['chars']} {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
