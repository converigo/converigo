"""
Project : Converigo
Founder : Pico Lala
Version : 1.0.0

Converter Registry

Single source of truth untuk seluruh converter.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(slots=True)
class ConverterInfo:
    id: str
    name: str
    category: str
    source_format: str
    target_format: str
    enabled: bool = True


class ConverterRegistry:

    def __init__(self) -> None:
        self._converters: Dict[str, ConverterInfo] = {}

    def register(self, converter: ConverterInfo) -> None:

        if converter.id in self._converters:
            raise ValueError(
                f"Converter '{converter.id}' already registered."
            )

        self._converters[converter.id] = converter

    def get(self, converter_id: str) -> ConverterInfo | None:
        return self._converters.get(converter_id)

    def get_all(self) -> List[ConverterInfo]:
        return list(self._converters.values())

    def get_by_category(
        self,
        category: str,
    ) -> List[ConverterInfo]:

        return [
            converter
            for converter in self._converters.values()
            if converter.category == category
        ]

    def count(self) -> int:
        return len(self._converters)


registry = ConverterRegistry()