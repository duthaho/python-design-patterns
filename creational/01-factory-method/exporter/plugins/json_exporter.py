from data_exporter import DataExporter, RegistryExporterCreator


class JSONExporter(DataExporter):
    def export(self, data: dict) -> None:
        print(f"Exporting data to JSON: {data}")


def register_exporters(registry: RegistryExporterCreator) -> None:
    registry.register_exporter("json", JSONExporter)
