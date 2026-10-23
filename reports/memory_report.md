# Memory Usage Comparison: Generators vs. Full Load

## Method

- Inputs generated with `python scripts/generate_large_samples.py --rows N` for N = 50,000, 100,000 and 200,000 (seed 42). At 200,000 rows the files are 12.8 MiB (CSV) and 23.1 MiB (XML).
- Measured with `python scripts/benchmark_memory.py` (`tracemalloc` peak, `time.perf_counter`):
  - **full load** = `len(handler.read(path)["entries"])`: parses, coerces and validates every entry into one `ConfigDocument`
  - **generator** = `sum(1 for _ in handler.iter_entries(path))`: one entry at a time, nothing kept
- Machine: Intel Core i7-10510U (4 cores / 8 threads, 1.8 GHz) / 31.7 GB RAM / Windows 11 (10.0.26100) · Python: 3.14.8
- `tracemalloc` counts only memory allocated by Python, not the interpreter's baseline, and slows execution while it runs. The memory figures are exact; treat the timings as relative, not absolute.
- JSON is not benchmarked: the `json` module can only parse a whole document, so `JsonHandler.iter_entries` loads the file first and saves no memory.

## Results

At 200,000 entries (the required run):

| Run | Entries | Peak MiB | Seconds |
|---|---:|---:|---:|
| large_config.csv full load | 200,000 | 120.03 | 4.09 |
| large_config.csv generator | 200,000 | 0.17 | 2.00 |
| large_config.xml full load | 200,000 | 211.22 | 6.73 |
| large_config.xml generator | 200,000 | 0.29 | 3.24 |

Peak MiB as the file grows:

| Entries | CSV full load | CSV generator | XML full load | XML generator |
|---:|---:|---:|---:|---:|
| 50,000 | 30.12 | 0.17 | 52.78 | 0.29 |
| 100,000 | 59.87 | 0.17 | 105.45 | 0.29 |
| 200,000 | 120.03 | 0.17 | 211.22 | 0.29 |

Extra runs at 200,000 entries to explain the numbers above:

| Run | Peak MiB | Seconds |
|---|---:|---:|
| CSV `list(iter_entries())`: entries kept, no validation | 83.53 | 2.29 |
| XML `list(iter_entries())`: entries kept, no validation | 83.57 | 3.80 |
| XML `iterparse`, no clearing | 135.49 | 3.20 |
| XML `iterparse`, `elem.clear()` only | 15.72 | 2.42 |
| XML `iterparse`, `elem.clear()` + detach from root (as implemented) | 0.27 | 2.36 |

## Analysis

### How peak memory scales with file size

- **Full load grows linearly.** Doubling the entries doubles the peak: CSV goes 30 → 60 → 120 MiB, about 0.6 KiB per entry, and XML goes 53 → 105 → 211 MiB, about 1.1 KiB per entry. In memory, the data takes roughly 9× its size on disk (12.8 MiB of CSV becomes 120 MiB) because every value becomes a Python object inside a dict.
- **The generator is constant.** It stays at 0.17 MiB (CSV) and 0.29 MiB (XML) whatever the file size: only the current entry, the reader's buffer and the parser state exist at any moment. At 200,000 entries that is about **700× less memory** than a full load, and the gap keeps widening as files grow.
- **Where the full-load memory goes.** Keeping 200,000 entry dicts costs 83.5 MiB in both formats, about 440 bytes per entry; that is the price of having every entry available at once. On top of that:
  - **CSV:** validation builds a cleaned copy of each entry while the originals are still referenced, which adds the remaining ~36 MiB.
  - **XML:** `ET.parse` first builds the whole element tree (135 MiB on its own, per the "no clearing" run), and the entry dicts are created while the tree still exists.

### Why `ET.iterparse` + `elem.clear()` keeps XML memory flat

`iterparse` emits events as it reads, so an `<entry>` can be turned into a dict as soon as its end tag arrives, without waiting for the rest of the file. But iterparse **still builds the tree as it goes**: every finished element stays attached to `<config>`. Without cleanup, memory grows exactly as with `ET.parse` (135 MiB).

- **`elem.clear()`** empties each finished element (its text, attributes and children), which removes most of the cost: 15.7 MiB. But the emptied element objects are still children of the root, so memory **still grows with file size**, just more slowly.
- **Clearing and also detaching the element from the root** (`del root[:]`) lets Python free it completely. Only the element being processed exists at any time, so memory is flat at 0.27 MiB.

The implementation in `XmlHandler.iter_entries` does both, and tracks nesting depth so that only `<entry>` elements directly under `<config>` count, matching `read()`.

### Trade-offs: generators vs. full load

| | Generator (`iter_entries`) | Full load (`read`) |
|---|---|---|
| Memory | Constant, independent of file size | Linear, about 9× file size |
| Access | Single pass, in order; a second pass must re-read the file | Random access (`entries[i]`), sort, index, re-iterate freely |
| Whole-document checks | Not possible while streaming (e.g. duplicate `section.key`, required metadata) | `validate_document` sees everything and reports every issue at once |
| Errors | Surface mid-iteration, after earlier entries were already consumed | Surface before any entry is used |
| Editing and writing | Can't modify in place | Needed by `ConfigTransaction`, `convert` and write-back |
| File handle | Stays open until the generator finishes or is closed | Closed once the read returns |
| Speed | Faster here, since nothing is stored or copied | Slower here, mostly because of the validation copy |

**Conclusion:** use `iter_entries()` for one-pass work over large files, such as counting, filtering or searching. Use `read()` when you need the whole document: validating it as a whole, editing it or converting it. The pipeline functions (`map`/`filter` in `pipeline.py`) are lazy, so they can be applied directly to `iter_entries()` without losing the memory benefit.
