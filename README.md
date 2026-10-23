# Configuration File Manager

Read configuration from **JSON, CSV and XML**, validate it against `TypedDict` schemas, convert between formats, and keep versioned backups. Built on the standard library only (`pathlib`, `json`, `csv`, `xml.etree.ElementTree`).

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Project Structure

```
src/config_manager/
├── schemas.py        # TypedDict schemas (ConfigDocument, ConfigEntry, ...)
├── protocols.py      # FormatHandler Protocol
├── handlers/         # JsonHandler, CsvHandler, XmlHandler + get_handler()
├── paths.py          # pathlib discovery, file inspection, ConfigTreeIterator
├── validation.py     # schema validation + type coercion
├── pipeline.py       # map()/filter() transformation pipeline
├── converter.py      # format conversion
├── transaction.py    # ConfigTransaction context manager
├── versioning.py     # timestamped backups in .versions/
└── cli.py            # `config-manager` command
samples/              # app_config.{json,csv,xml}; large/ for generated benchmark files
scripts/              # generate_large_samples.py, benchmark_memory.py
reports/              # memory_report.md
tests/                # pytest suite + fixtures/
```

## Format Support Matrix

| Format | Extension | Read | Write | Streaming (`iter_entries`) | Library | Metadata stored as |
|---|---|:-:|:-:|:-:|---|---|
| JSON | `.json` | ✅ | ✅ | ✅\* | `json` | `"metadata"` object |
| CSV  | `.csv`  | ✅ | ✅ | ✅ | `csv.DictReader` / `DictWriter` | `# key=value` header comments |
| XML  | `.xml`  | ✅ | ✅ | ✅ | `xml.etree.ElementTree` (`iterparse`) | `<config>` attributes + `<description>` |

\* The `json` module can only parse a whole document, so `JsonHandler.iter_entries` yields entries after loading the file: same interface, no memory saving.

## Schema Definitions

Defined in [`src/config_manager/schemas.py`](src/config_manager/schemas.py).

```python
ValueType = Literal["str", "int", "float", "bool"]

class ConfigEntry(TypedDict):
    section: str
    key: str
    value: str | int | float | bool
    type: ValueType
    description: NotRequired[str]

class ConfigMetadata(TypedDict):
    name: str
    version: str
    description: NotRequired[str]

class ConfigDocument(TypedDict):
    metadata: ConfigMetadata
    entries: list[ConfigEntry]
```

**Validation rules**

- `metadata.name` and `metadata.version` are required
- every entry needs `section`, `key`, `value`, `type`
- `type` must be one of `str | int | float | bool`, and `value` must match it
- CSV/XML values are strings on disk and are coerced using `type`

## Format Examples

The same document in each format (see [`samples/`](samples/)):

**JSON**
```json
{"metadata": {"name": "app", "version": "1.0.0"},
 "entries": [{"section": "database", "key": "port", "value": 5432, "type": "int"}]}
```

**CSV**
```csv
# name=app
# version=1.0.0
section,key,value,type,description
database,port,5432,int,
```

**XML**
```xml
<config name="app" version="1.0.0">
  <entry section="database" key="port" type="int">5432</entry>
</config>
```

## Conversion Examples

```bash
config-manager convert samples/app_config.json out/app_config.xml
config-manager convert samples/app_config.csv  out/app_config.json
config-manager validate samples/app_config.xml
config-manager discover samples/
config-manager version save samples/app_config.json
config-manager version list samples/app_config.json
config-manager version restore samples/app_config.json -n 1
```

```python
from pathlib import Path
from config_manager.converter import convert
from config_manager.pipeline import compose, filter_valid, select_section

convert(Path("samples/app_config.json"), Path("out/database.csv"),
        transform=compose(filter_valid, select_section("database")))
```

```python
from config_manager.transaction import ConfigTransaction

with ConfigTransaction(Path("samples/app_config.json")) as doc:
    doc["metadata"]["version"] = "1.1.0"   # written atomically on exit
```

## Memory Efficiency

```bash
python scripts/generate_large_samples.py --rows 200000
python scripts/benchmark_memory.py
```

At 200,000 entries, streaming with `iter_entries()` peaks at **0.17 MiB (CSV)** and **0.29 MiB (XML)**, against 120 MiB and 211 MiB for a full `read()`. Streaming memory stays constant as files grow, while a full load grows linearly with file size.

Results and analysis: [`reports/memory_report.md`](reports/memory_report.md).

## Testing

```bash
pytest                                   # all tests
pytest --cov=config_manager              # with coverage
mypy src && ruff check .                 # type check + lint
```

## Milestones

- [x] Day 1–2 — pathlib file ops, JSON reader/writer, file discovery
- [x] Day 3–4 — CSV parser, XML parser, format conversion
- [x] Day 5–6 — TypedDict validation, Protocol handlers, transactions, versioning
- [x] Day 7 — generators, pytest suite per format, memory report
