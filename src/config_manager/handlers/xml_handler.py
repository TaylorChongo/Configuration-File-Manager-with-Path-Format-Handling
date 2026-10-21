"""XML reader/writer using ``xml.etree.ElementTree``.

File layout::

    <config name="app" version="1.0.0">
      <description>...</description>
      <entry section="database" key="host" type="str">localhost</entry>
    </config>
"""

from collections.abc import Iterator
from pathlib import Path

from config_manager.schemas import ConfigDocument, ConfigEntry


class XmlHandler:
    extensions: tuple[str, ...] = (".xml",)

    def read(self, path: Path) -> ConfigDocument:
        # TODO (Day 3-4): ET.parse, read root attributes, collect <entry> elements
        raise NotImplementedError

    def write(self, document: ConfigDocument, path: Path) -> None:
        # TODO (Day 3-4): build tree, ET.indent, tree.write(encoding="utf-8", xml_declaration=True)
        raise NotImplementedError

    def iter_entries(self, path: Path) -> Iterator[ConfigEntry]:
        # TODO (Day 7): ET.iterparse(events=("end",)); yield on each <entry>,
        # then elem.clear() to release memory
        raise NotImplementedError
