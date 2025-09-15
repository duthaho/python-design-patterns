import random
import time
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ServiceSpec:
    name: str
    version: str
    replicas: int = 2


class Logger:
    def info(self, msg: str, **kw):
        print(f"[INFO] {msg}", kw if kw else "")

    def error(self, msg: str, **kw):
        print(f"[ERROR] {msg}", kw if kw else "")


class RetryPolicy:
    def __init__(self, retries: int = 3, backoff: float = 1.0) -> None:
        self.retries = retries
        self.backoff = backoff

    def run(self, fn: Callable[[], Any]) -> Any:
        attempt = 0
        while attempt < self.retries:
            try:
                return fn()
            except Exception as e:
                attempt += 1
                if attempt == self.retries:
                    raise
                sleep_time = self.backoff * (2 ** (attempt - 1)) + random.uniform(
                    0, 0.1
                )
                time.sleep(sleep_time)


class CircuitBreaker:
    def __init__(self, threshold: int = 5, cooldown: float = 60.0) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.open_until = 0.0

    def call(self, fn: Callable[[], Any]) -> Any:
        current_time = time.time()
        if current_time < self.open_until:
            raise Exception("Circuit is open")
        try:
            result = fn()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.open_until = current_time + self.cooldown
            raise


class MetricsRecorder:
    def incr(self, name: str, **labels) -> None:
        print("METRIC", name, labels)

    def timing(self, name: str, duration_ms: float, **labels) -> None:
        print("TIMING", name, duration_ms, labels)


class InfraProvisioner:
    def provision_db(self) -> None:
        print("Provisioning database...")

    def provision_cache(self) -> None:
        print("Provisioning cache...")

    def teardown_db(self) -> None:
        print("Tearing down database...")

    def teardown_cache(self) -> None:
        print("Tearing down cache...")


class ImageBuilder:
    def build(self, spec: ServiceSpec) -> str:
        print(f"Building image for {spec.name}:{spec.version}...")
        return f"{spec.name}:{spec.version}"

    def push(self, image: str) -> None:
        print(f"Pushing image {image} to registry...")


class Deployer:
    def apply_manifests(self, image: str, spec: ServiceSpec) -> None:
        print(f"Applying manifests for {spec.name} with image {image}...")

    def rollout(self, spec: ServiceSpec) -> None:
        print(f"Rolling out {spec.replicas} replicas of {spec.name}...")

    def remove_manifests(self, spec: ServiceSpec) -> None:
        print(f"Removing manifests for {spec.name}...")


class HealthChecker:
    def wait_until_ready(self, spec: ServiceSpec, timeout: float = 300.0) -> bool:
        current_time = 0.0
        interval = 5.0
        while current_time < timeout:
            print(f"Checking health of {spec.name}...")
            if random.random() < 0.7:  # 70% chance to be healthy
                print(f"{spec.name} is healthy!")
                return True
            time.sleep(interval)
            current_time += interval
        return False


class Notifier:
    def notify(self, message: str) -> None:
        print(f"NOTIFICATION: {message}")


class DeploymentFacade:
    def __init__(
        self,
        infra: InfraProvisioner,
        builder: ImageBuilder,
        deployer: Deployer,
        health: HealthChecker,
        notify: Notifier,
        metrics: MetricsRecorder,
        retry: RetryPolicy,
        breaker: CircuitBreaker,
        logger: Logger,
    ):
        self.infra = infra
        self.builder = builder
        self.deployer = deployer
        self.health = health
        self.notify = notify
        self.metrics = metrics
        self.retry = retry
        self.breaker = breaker
        self.logger = logger

    def deploy_service(self, spec: ServiceSpec):
        start_time = time.time()
        try:
            self.logger.info("Starting deployment", service=spec.name)

            # Provision infra with retries and breaker
            self.breaker.call(lambda: self.retry.run(self.infra.provision_db))
            self.breaker.call(lambda: self.retry.run(self.infra.provision_cache))

            # Build and push image
            image = self.builder.build(spec)
            self.breaker.call(lambda: self.retry.run(lambda: self.builder.push(image)))

            # Deploy
            self.deployer.apply_manifests(image, spec)
            self.deployer.rollout(spec)

            # Health check
            if not self.retry.run(lambda: self.health.wait_until_ready(spec)):
                raise Exception("Service failed to become healthy")

            self.notify.notify(f"Service {spec.name} deployed successfully!")
            self.metrics.incr("service_deploy_success_total", service=spec.name)
            self.logger.info("Deployment completed", service=spec.name)

        except Exception as e:
            self.logger.error("Deployment failed", service=spec.name, error=str(e))
            self.rollback(spec)
            self.metrics.incr("service_deploy_failure_total", service=spec.name)
            self.notify.notify(f"Service {spec.name} deployment failed: {str(e)}")
            raise
        finally:
            duration = (time.time() - start_time) * 1000
            self.metrics.timing(
                "service_deploy_duration_ms", duration, service=spec.name
            )

    def rollback(self, spec: ServiceSpec):
        self.logger.info("Rolling back deployment", service=spec.name)
        try:
            self.deployer.remove_manifests(spec)
            self.infra.teardown_cache()
            self.infra.teardown_db()
            self.notify.notify(f"Rollback completed for {spec.name}")
        except Exception as e:
            self.logger.error(
                "Rollback encountered errors", service=spec.name, error=str(e)
            )
            self.notify.notify(f"Rollback failed for {spec.name}: {str(e)}")


if __name__ == "__main__":
    infra = InfraProvisioner()
    builder = ImageBuilder()
    deployer = Deployer()
    health = HealthChecker()
    notify = Notifier()
    metrics = MetricsRecorder()
    retry = RetryPolicy(retries=3, backoff=2.0)
    breaker = CircuitBreaker(threshold=3, cooldown=30.0)
    logger = Logger()

    facade = DeploymentFacade(
        infra, builder, deployer, health, notify, metrics, retry, breaker, logger
    )

    service_spec = ServiceSpec(name="orders", version="1.2.3", replicas=3)
    facade.deploy_service(service_spec)
