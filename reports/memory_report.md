# Memory Usage Comparison: Generators vs. Full Load

> Fill in after Day 7 once `iter_entries()` is implemented for each handler.

## Method

- Inputs generated with `python scripts/generate_large_samples.py --rows 200000`
- Measured with `python scripts/benchmark_memory.py` (`tracemalloc` peak, `time.perf_counter`)
- Machine: _CPU / RAM / OS_ · Python: _version_

## Results

| Run | Entries | Peak MiB | Seconds |
|---|---:|---:|---:|
| large_config.csv full load | | | |
| large_config.csv generator | | | |
| large_config.xml full load | | | |
| large_config.xml generator | | | |

## Analysis

- _How peak memory scales with file size for each approach_
- _Why `ET.iterparse` + `elem.clear()` keeps XML memory flat_
- _Trade-offs: generators are single-pass; full load allows random access_
