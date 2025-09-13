from abc import ABC, abstractmethod
from typing import Dict, List, Tuple


class CloudProvider:
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class ResourceStatus:
    CREATING = "creating"
    AVAILABLE = "available"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class Compute(ABC):
    @abstractmethod
    def create_instance(self, name: str, size: str) -> None: ...

    @abstractmethod
    def get_instance_info(self) -> Dict: ...

    @abstractmethod
    def get_estimated_cost_per_hour(self, size: str) -> float: ...


class Storage(ABC):
    @abstractmethod
    def create_bucket(self, name: str, versioning: bool) -> None: ...

    @abstractmethod
    def get_bucket_info(self) -> Dict: ...


class Queue(ABC):
    @abstractmethod
    def create_queue(self, name: str, fifo: bool) -> None: ...

    @abstractmethod
    def get_queue_info(self) -> Dict: ...


class CloudFactory(ABC):
    @abstractmethod
    def create_compute(self) -> Compute: ...

    @abstractmethod
    def create_storage(self) -> Storage: ...

    @abstractmethod
    def create_queue(self) -> Queue: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...

    @abstractmethod
    def get_supported_regions(self) -> List[str]: ...


class AWSCompute(Compute):
    def __init__(self):
        self.instances = {}

    def create_instance(self, name: str, size: str) -> None:
        print(f"AWS: Creating EC2 instance '{name}' of size '{size}'")
        self.instances[name] = {"size": size, "status": ResourceStatus.CREATING}
        # Simulate instance becoming available
        self.instances[name]["status"] = ResourceStatus.AVAILABLE

    def get_instance_info(self) -> Dict:
        return dict(provider=CloudProvider.AWS, service="EC2", instances=self.instances)

    def get_estimated_cost_per_hour(self, size: str) -> float:
        pricing = {"t2.micro": 0.0116, "t2.small": 0.023, "t2.medium": 0.0464}
        return pricing.get(size, 0.05)


class AWSStorage(Storage):
    def __init__(self):
        self.buckets = {}

    def create_bucket(self, name: str, versioning: bool) -> None:
        print(f"AWS: Creating S3 bucket '{name}' with versioning={versioning}")

    def get_bucket_info(self) -> Dict:
        return dict(provider=CloudProvider.AWS, service="S3", buckets=self.buckets)


class AWSQueue(Queue):
    def __init__(self):
        self.queues = {}

    def create_queue(self, name: str, fifo: bool) -> None:
        print(f"AWS: Creating SQS queue '{name}' with fifo={fifo}")

    def get_queue_info(self) -> Dict:
        return dict(provider=CloudProvider.AWS, service="SQS", queues=self.queues)


class AWSFactory(CloudFactory):
    def create_compute(self) -> Compute:
        return AWSCompute()

    def create_storage(self) -> Storage:
        return AWSStorage()

    def create_queue(self) -> Queue:
        return AWSQueue()

    def get_provider_name(self) -> str:
        return CloudProvider.AWS

    def get_supported_regions(self) -> List[str]:
        return ["us-east-1", "us-west-2", "eu-west-1"]


class AzureCompute(Compute):
    def __init__(self):
        self.instances = {}

    def create_instance(self, name: str, size: str) -> None:
        print(f"Azure: Creating VM instance '{name}' of size '{size}'")
        self.instances[name] = {"size": size, "status": ResourceStatus.CREATING}
        # Simulate instance becoming available
        self.instances[name]["status"] = ResourceStatus.AVAILABLE

    def get_instance_info(self) -> Dict:
        return dict(
            provider=CloudProvider.AZURE, service="VM", instances=self.instances
        )

    def get_estimated_cost_per_hour(self, size: str) -> float:
        pricing = {"B1s": 0.012, "B2s": 0.04, "D2s_v3": 0.096}
        return pricing.get(size, 0.05)


class AzureStorage(Storage):
    def __init__(self):
        self.buckets = {}

    def create_bucket(self, name: str, versioning: bool) -> None:
        print(
            f"Azure: Creating Blob Storage container '{name}' with versioning={versioning}"
        )

    def get_bucket_info(self) -> Dict:
        return dict(
            provider=CloudProvider.AZURE, service="Blob Storage", buckets=self.buckets
        )


class AzureQueue(Queue):
    def __init__(self):
        self.queues = {}

    def create_queue(self, name: str, fifo: bool) -> None:
        if fifo:
            raise ValueError("Azure Queue does not support FIFO queues.")
        print(f"Azure: Creating Queue '{name}'")

    def get_queue_info(self) -> Dict:
        return dict(provider=CloudProvider.AZURE, service="Queue", queues=self.queues)


class AzureFactory(CloudFactory):
    def create_compute(self) -> Compute:
        return AzureCompute()

    def create_storage(self) -> Storage:
        return AzureStorage()

    def create_queue(self) -> Queue:
        return AzureQueue()

    def get_provider_name(self) -> str:
        return CloudProvider.AZURE

    def get_supported_regions(self) -> List[str]:
        return ["eastus", "westus2", "northeurope"]


class CloudFactoryRegistry:
    factories: Dict[str, CloudFactory] = {
        CloudProvider.AWS: AWSFactory,
        CloudProvider.AZURE: AzureFactory,
    }

    @classmethod
    def register_factory(cls, factory: CloudFactory) -> None:
        cls.factories[factory.get_provider_name()] = factory

    @classmethod
    def get_factory(cls, provider_name: str) -> CloudFactory:
        if provider_name not in cls.list_providers():
            raise ValueError(f"Provider '{provider_name}' is not supported.")
        return cls.factories[provider_name]()

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls.factories.keys())


class Provisioner:
    def __init__(self, factory: CloudFactory):
        self.factory = factory
        self.audit: List[str] = []
        self.created_resources: Dict[str, Dict] = {}
        self.total_estimated_cost = 0.0

    def validate_config(self, config: Dict) -> Tuple[bool, str]:
        errors = []

        if "compute" in config:
            compute_cfg = config["compute"]
            if "name" not in compute_cfg or not compute_cfg["name"]:
                errors.append("Compute instance must have a valid name.")
            if "size" not in compute_cfg or not compute_cfg["size"]:
                errors.append("Compute instance must have a valid size.")

            region = compute_cfg.get("region", "us-east-1")
            if region not in self.factory.get_supported_regions():
                errors.append(
                    f"Region '{region}' is not supported by {self.factory.get_provider_name()}."
                )

        if "storage" in config:
            storage_cfg = config["storage"]
            if "name" not in storage_cfg or not storage_cfg["name"]:
                errors.append("Storage bucket must have a valid name.")
            if "versioning" not in storage_cfg:
                errors.append("Storage bucket must specify versioning (True/False).")

        if "queue" in config:
            queue_cfg = config["queue"]
            if "name" not in queue_cfg or not queue_cfg["name"]:
                errors.append("Queue must have a valid name.")
            if "fifo" not in queue_cfg:
                errors.append("Queue must specify fifo (True/False).")
            elif (
                queue_cfg["fifo"]
                and self.factory.get_provider_name() == CloudProvider.AZURE
            ):
                errors.append("Azure Queue does not support FIFO queues.")

        return errors

    def _provision_compute(self, cfg: Dict) -> None:
        compute = self.factory.create_compute()
        compute.create_instance(cfg["name"], cfg["size"])
        self.created_resources["compute"] = compute.get_instance_info()
        cost = compute.get_estimated_cost_per_hour(cfg["size"])
        self.total_estimated_cost += cost
        self.audit.append(
            f"Provisioned Compute: {cfg['name']} (Size: {cfg['size']}, Est. Cost/hr: ${cost:.4f})"
        )

    def _provision_storage(self, cfg: Dict) -> None:
        storage = self.factory.create_storage()
        storage.create_bucket(cfg["name"], cfg["versioning"])
        self.created_resources["storage"] = storage.get_bucket_info()
        self.audit.append(
            f"Provisioned Storage: {cfg['name']} (Versioning: {cfg['versioning']})"
        )

    def _provision_queue(self, cfg: Dict) -> None:
        queue = self.factory.create_queue()
        queue.create_queue(cfg["name"], cfg["fifo"])
        self.created_resources["queue"] = queue.get_queue_info()
        self.audit.append(f"Provisioned Queue: {cfg['name']} (FIFO: {cfg['fifo']})")

    def cleanup(self) -> None:
        print("Cleaning up created resources...")
        for rtype, resources in self.created_resources.items():
            if resources:
                self.audit.append(f"Deleted {rtype} resources.")
        self.audit.append("Cleaned up all created resources.")
        self.total_estimated_cost = 0.0

    def provision(self, config: Dict) -> Dict:
        validation_errors = self.validate_config(config)
        if validation_errors:
            return {
                "status": "failed",
                "errors": validation_errors,
                "audit": self.audit,
            }

        try:
            if "compute" in config:
                self._provision_compute(config["compute"])
            if "storage" in config:
                self._provision_storage(config["storage"])
            if "queue" in config:
                self._provision_queue(config["queue"])

            return {
                "status": "success",
                "created_resources": self.created_resources,
                "total_estimated_monthly_cost": self.total_estimated_cost * 24 * 30,
                "audit": self.audit,
            }
        except Exception as e:
            self.cleanup()
            self.audit.append(f"Provisioning failed: {str(e)}")

            return {"status": "failed", "errors": [str(e)], "audit": self.audit}


def demo_provisioning():
    print("Available Cloud Providers:", CloudFactoryRegistry.list_providers())

    aws_factory = CloudFactoryRegistry.get_factory(CloudProvider.AWS)
    azure_factory = CloudFactoryRegistry.get_factory(CloudProvider.AZURE)

    aws_provisioner = Provisioner(aws_factory)
    azure_provisioner = Provisioner(azure_factory)

    deployment_config = {
        CloudProvider.AWS: {
            "compute": {
                "name": "aws-web-server",
                "size": "t2.micro",
                "region": "us-east-1",
            },
            "storage": {"name": "aws-app-bucket", "versioning": True},
            "queue": {"name": "aws-task-queue", "fifo": False},
        },
        CloudProvider.AZURE: {
            "compute": {"name": "azure-web-server", "size": "B1s", "region": "eastus"},
            "storage": {"name": "azure-app-bucket", "versioning": False},
            "queue": {"name": "azure-task-queue", "fifo": False},
        },
    }

    for provider, config in deployment_config.items():
        print(f"\nProvisioning resources on {provider}...")
        provisioner = (
            aws_provisioner if provider == CloudProvider.AWS else azure_provisioner
        )
        result = provisioner.provision(config)
        if result["status"] == "success":
            print("Provisioning succeeded.")
            print("Created Resources:", result["created_resources"])
            print(
                f"Estimated Monthly Cost: ${result['total_estimated_monthly_cost']:.2f}"
            )
        else:
            print("Provisioning failed with errors:", result.get("errors", []))
        print("Audit Log:")
        for log in result["audit"]:
            print(" -", log)


if __name__ == "__main__":
    demo_provisioning()
