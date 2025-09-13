import importlib
from abc import ABC, abstractmethod
from typing import Dict, Type


class DataExporter(ABC):
    @abstractmethod
    def export(self, data: dict) -> None:
        pass


class RegistryExporterCreator:
    def __init__(self):
        self._registry: Dict[str, Type[DataExporter]] = {}

    def register_exporter(
        self, format_name: str, exporter_cls: Type[DataExporter]
    ) -> None:
        self._registry[format_name] = exporter_cls

    def create_exporter(self, format_name: str) -> DataExporter:
        exporter_cls = self._registry.get(format_name)
        if not exporter_cls:
            available = ", ".join(self._registry.keys())
            raise ValueError(
                f"Exporter for format '{format_name}' is not registered. Available formats: {available}"
            )
        return exporter_cls()

    def render(self, format_name: str, data: dict) -> None:
        exporter = self.create_exporter(format_name)
        exporter.export(data)


def load_plugins(modules: list, registry: RegistryExporterCreator) -> None:
    for module in modules:
        try:
            mod = importlib.import_module(module)
            if hasattr(mod, "register_exporters"):
                mod.register_exporters(registry)
            else:
                print(f"Module {module} does not have 'register_exporters' function.")
        except Exception as e:
            print(f"Failed to load module {module}: {e}")


# Application code
def main() -> None:
    registry = RegistryExporterCreator()

    # List of plugin modules to load
    plugins = [
        "plugins.csv_exporter",
        "plugins.json_exporter",
    ]

    load_plugins(plugins, registry)

    # Example usage
    data = {"name": "John", "age": 30}

    for format_name in ["csv", "json", "xml"]:
        try:
            registry.render(format_name, data)
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    main()
