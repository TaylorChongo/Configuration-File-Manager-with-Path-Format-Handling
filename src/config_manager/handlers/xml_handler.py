"""XML reader/writer using ``xml.etree.ElementTree``.

File layout::

    <config name="app" version="1.0.0">
      <description>...</description>
      <entry section="database" key="host" type="str">localhost</entry>
    </config>
"""

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from pathlib import Path
from typing import cast

from config_manager.schemas import ConfigDocument, ConfigEntry, ConfigMetadata, ValueType
from config_manager.validation import coerce_value, entry_to_strings

REQUIRED_ATTRIBUTES: tuple[str, ...] = ("section", "key", "type")


def element_to_entry(elem: ET.Element, location: str) -> ConfigEntry:
    """Convert an ``<entry>`` element into a coerced ``ConfigEntry``."""
    missing = [name for name in REQUIRED_ATTRIBUTES if name not in elem.attrib]
    if missing:
        raise ValueError(f"{location}: missing attributes: {', '.join(missing)}")
    value_type = cast(ValueType, elem.attrib["type"])
    try:
        value = coerce_value(elem.text or "", value_type)
    except ValueError as exc:
        raise ValueError(f"{location}: {exc}") from None
    entry: ConfigEntry = {
        "section": elem.attrib["section"],
        "key": elem.attrib["key"],
        "value": value,
        "type": value_type,
    }
    if elem.attrib.get("description"):
        entry["description"] = elem.attrib["description"]
    return entry


def entry_to_element(entry: ConfigEntry) -> ET.Element:
    """Convert a ``ConfigEntry`` into an ``<entry>`` element (value as text)."""
    flat = entry_to_strings(entry)
    attrs = {name: flat[name] for name in ("section", "key", "type")}
    if flat["description"]:
        attrs["description"] = flat["description"]
    elem = ET.Element("entry", attrs)
    elem.text = flat["value"]
    return elem


class XmlHandler:
    extensions: tuple[str, ...] = (".xml",)

    def read(self, path: Path) -> ConfigDocument:
        root = ET.parse(path).getroot()
        if root.tag != "config":
            raise ValueError(f"{path}: root element must be <config>, got <{root.tag}>")
        metadata: dict[str, str] = dict(root.attrib)
        description = root.find("description")
        if description is not None and description.text:
            metadata["description"] = description.text
        entries = [
            element_to_entry(elem, f"{path}, entry {index}")
            for index, elem in enumerate(root.iterfind("entry"), start=1)
        ]
        # TODO (Day 5-6): validate metadata via validate_document
        return {"metadata": cast(ConfigMetadata, metadata), "entries": entries}

    def write(self, document: ConfigDocument, path: Path) -> None:
        metadata = document["metadata"]
        root = ET.Element("config", {"name": metadata["name"], "version": metadata["version"]})
        if "description" in metadata:
            ET.SubElement(root, "description").text = metadata["description"]
        root.extend(map(entry_to_element, document["entries"]))

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as fh:
            tree.write(fh, encoding="utf-8", xml_declaration=True)
            fh.write(b"\n")

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        # TODO (Day 7): ET.iterparse(events=("end",)); yield on each <entry>,
        # then elem.clear() to release memory
        raise NotImplementedError
