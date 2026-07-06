from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Type

if TYPE_CHECKING:
    from app.engines.base_engine import BaseEngine
else:
    BaseEngine = object


class EngineRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseEngine]] = {}

    def register_engine(self, engine_class: Type[BaseEngine]) -> None:
        engine_name = engine_class.ENGINE_NAME
        if engine_name in self._registry:
            raise ValueError(f"Engine '{engine_name}' is already registered.")
        self._registry[engine_name] = engine_class

    def get_engine_class(self, engine_name: str) -> Type[BaseEngine]:
        try:
            return self._registry[engine_name]
        except KeyError as exc:
            raise ValueError(f"Engine '{engine_name}' is not registered.") from exc

    def create_engine(self, engine_name: str, metadata: Optional[dict] = None) -> BaseEngine:
        engine_class = self.get_engine_class(engine_name)
        return engine_class(metadata=metadata)

    def find_engine_for_format(self, file_format: str) -> Type[BaseEngine]:
        normalized_format = file_format.lower().lstrip(".")
        for engine_class in self._registry.values():
            if engine_class.supports_format(normalized_format):
                return engine_class

        raise ValueError(f"No engine supports format '{file_format}'.")

    def list_engines(self) -> List[str]:
        return sorted(self._registry.keys())


ENGINE_REGISTRY = EngineRegistry()


class ConversionManager:
    def __init__(self, registry: EngineRegistry = ENGINE_REGISTRY) -> None:
        self.registry = registry

    def create_engine(self, engine_name: str, metadata: Optional[dict] = None) -> BaseEngine:
        _ensure_builtin_engines_registered()
        return self.registry.create_engine(engine_name, metadata)

    def create_engine_for_format(self, file_format: str, metadata: Optional[dict] = None) -> BaseEngine:
        _ensure_builtin_engines_registered()
        engine_class = self.registry.find_engine_for_format(file_format)
        return engine_class(metadata=metadata)

    def available_engines(self) -> List[str]:
        _ensure_builtin_engines_registered()
        return self.registry.list_engines()


def register_engine(engine_class: Type[BaseEngine]) -> None:
    ENGINE_REGISTRY.register_engine(engine_class)


def _ensure_builtin_engines_registered() -> None:
    if not ENGINE_REGISTRY._registry:
        import importlib

        importlib.import_module("app.engines")


def _get_engine_class(engine_name: str) -> Type[BaseEngine]:
    _ensure_builtin_engines_registered()
    return ENGINE_REGISTRY.get_engine_class(engine_name)


def _list_engines() -> List[str]:
    _ensure_builtin_engines_registered()
    return ENGINE_REGISTRY.list_engines()


# Backwards-compatibility helpers for internal module use.
get_engine_class = _get_engine_class
list_engines = _list_engines
