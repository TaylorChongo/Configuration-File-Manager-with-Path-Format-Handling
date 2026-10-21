"""Compare peak memory: generator (iter_entries) vs. full load (read).

Run scripts/generate_large_samples.py first, then:
    python scripts/benchmark_memory.py
Paste the resulting table into reports/memory_report.md.
"""

import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path

from config_manager.handlers import get_handler
from config_manager.protocols import FormatHandler

LARGE_DIR = Path(__file__).resolve().parent.parent / "samples" / "large"


def measure(label: str, fn: Callable[[], int]) -> tuple[str, int, float, float]:
    """Return (label, entry count, peak MiB, seconds)."""
    tracemalloc.start()
    start = time.perf_counter()
    count = fn()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return label, count, peak / 1_048_576, elapsed


def main() -> None:
    results = []
    for path in sorted(LARGE_DIR.glob("large_config.*")):
        handler = get_handler(path)

        def full_load(h: FormatHandler = handler, p: Path = path) -> int:
            return len(h.read(p)["entries"])

        def stream(h: FormatHandler = handler, p: Path = path) -> int:
            return sum(1 for _ in h.iter_entries(p))

        results.append(measure(f"{path.name} full load", full_load))
        results.append(measure(f"{path.name} generator", stream))

    print(f"| {'Run':<32} | {'Entries':>9} | {'Peak MiB':>9} | {'Seconds':>8} |")
    print(f"|{'-' * 34}|{'-' * 11}|{'-' * 11}|{'-' * 10}|")
    for label, count, peak, secs in results:
        print(f"| {label:<32} | {count:>9,} | {peak:>9.2f} | {secs:>8.2f} |")


if __name__ == "__main__":
    main()
