"""Generate large CSV/XML config files for generator memory benchmarks.

Usage: python scripts/generate_large_samples.py [--rows 200000]
"""

import argparse
import csv
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT_DIR = Path(__file__).resolve().parent.parent / "samples" / "large"
SECTIONS = ("database", "server", "cache", "logging", "auth", "features")
FIELDNAMES = ("section", "key", "value", "type", "description")


def random_entry(i: int, rng: random.Random) -> dict[str, str]:
    value_type = rng.choice(("str", "int", "float", "bool"))
    value = {
        "str": f"value_{i}",
        "int": str(rng.randint(0, 65535)),
        "float": f"{rng.uniform(0, 1000):.3f}",
        "bool": rng.choice(("true", "false")),
    }[value_type]
    return {
        "section": rng.choice(SECTIONS),
        "key": f"setting_{i}",
        "value": value,
        "type": value_type,
        "description": f"Generated setting number {i}",
    }


def write_csv(path: Path, rows: int, rng: random.Random) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        fh.write("# name=large\n# version=1.0.0\n")
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        for i in range(rows):
            writer.writerow(random_entry(i, rng))


def write_xml(path: Path, rows: int, rng: random.Random) -> None:
    # Streamed by hand so generating the file doesn't itself need the whole tree in memory.
    with path.open("w", encoding="utf-8") as fh:
        fh.write("<?xml version='1.0' encoding='utf-8'?>\n")
        fh.write('<config name="large" version="1.0.0">\n')
        for i in range(rows):
            e = random_entry(i, rng)
            fh.write(
                f'  <entry section="{e["section"]}" key="{e["key"]}" type="{e["type"]}" '
                f'description="{escape(e["description"])}">{escape(e["value"])}</entry>\n'
            )
        fh.write("</config>\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=200_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    for suffix, writer in ((".csv", write_csv), (".xml", write_xml)):
        target = OUT_DIR / f"large_config{suffix}"
        writer(target, args.rows, rng)
        print(f"wrote {target} ({target.stat().st_size / 1_048_576:.1f} MiB)")


if __name__ == "__main__":
    main()
