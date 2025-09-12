from abc import ABC, abstractmethod
from typing import Dict, Type


class Exporter(ABC):
    @abstractmethod
    def export(self, text: str) -> str:
        pass


class PdfExporter(Exporter):
    def export(self, text: str) -> str:
        return f"PDF <<{text}>>"


class MarkdownExporter(Exporter):
    def export(self, text: str) -> str:
        return f"Markdown # {text}"


class HtmlExporter(Exporter):
    def export(self, text: str) -> str:
        return f"<h1>{text}</h1>"


class ExporterCreator(ABC):
    @abstractmethod
    def create_exporter(self) -> Exporter:
        pass

    def render(self, text: str) -> str:
        exporter = self.create_exporter()
        return exporter.export(text)


class PdfExporterCreator(ExporterCreator):
    def create_exporter(self) -> Exporter:
        return PdfExporter()


class MarkdownExporterCreator(ExporterCreator):
    def create_exporter(self) -> Exporter:
        return MarkdownExporter()


class HtmlExporterCreator(ExporterCreator):
    def create_exporter(self) -> Exporter:
        return HtmlExporter()


class RegistryExporterCreator:
    def __init__(self):
        self._registry: Dict[str, Type[ExporterCreator]] = {}

    def register_exporter(
        self, format_name: str, creator_cls: Type[ExporterCreator]
    ) -> None:
        self._registry[format_name] = creator_cls

    def create_exporter(self, format_name: str) -> ExporterCreator:
        creator_cls = self._registry.get(format_name)
        if not creator_cls:
            available = ", ".join(self._registry.keys())
            raise ValueError(
                f"Exporter for format '{format_name}' is not registered. Available formats: {available}"
            )
        return creator_cls()

    def render(self, format_name: str, text: str) -> str:
        creator = self.create_exporter(format_name)
        return creator.render(text)


# Application code
def render_document(
    registry: RegistryExporterCreator, format_name: str, text: str
) -> None:
    return registry.render(format_name, text)


def main() -> None:
    registry = RegistryExporterCreator()
    exporters = {
        "pdf": PdfExporterCreator,
        "markdown": MarkdownExporterCreator,
        "html": HtmlExporterCreator,
    }
    for format_name, creator_cls in exporters.items():
        registry.register_exporter(format_name, creator_cls)

    # Example usage
    text = "Hello, World!"

    for format_name in ["pdf", "markdown", "html", "docx"]:
        try:
            result = render_document(registry, format_name, text)
            print(f"Rendered in {format_name}:\n{result}\n")
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    main()
