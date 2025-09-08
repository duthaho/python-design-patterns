from data_exporter import DataExporter, RegistryExporterCreator


class CSVExporter(DataExporter):
    def export(self, data: dict) -> None:
        print("Exporting data in CSV format:")
        for key, value in data.items():
            print(f"{key},{value}")


def register_exporters(registry: RegistryExporterCreator) -> None:
    registry.register_exporter("csv", CSVExporter)
    