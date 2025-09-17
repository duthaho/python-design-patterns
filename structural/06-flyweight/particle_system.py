import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class ParticleFlyweight:
    type: str
    texture: str
    size: float
    color: str

    def render(
        self,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
        age: float,
        lifetime: float,
    ) -> None:
        # In a real game engine, this would render to screen
        alpha = max(0.0, 1.0 - (age / lifetime))  # Fade out over time
        print(
            f"Rendering {self.type}: pos={position}, vel={velocity:.1f}, "
            f"alpha={alpha:.2f}, size={self.size}, color={self.color}"
        )

    def update_physics(
        self,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
        delta_time: float,
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Update physics and return new position and velocity"""
        # Apply simple physics (gravity, air resistance, etc.)
        gravity = -9.8
        air_resistance = 0.99

        new_velocity = (
            velocity[0] * air_resistance,
            velocity[1] * air_resistance + gravity * delta_time,
        )

        new_position = (
            position[0] + new_velocity[0] * delta_time,
            position[1] + new_velocity[1] * delta_time,
        )

        return new_position, new_velocity


class ParticleFactory:
    _flyweights: dict[Tuple[str, str, float, str], ParticleFlyweight] = {}
    _creation_count = 0  # Track total creations for memory stats

    @classmethod
    def get_flyweight(
        cls, particle_type: str, texture: str, size: float, color: str
    ) -> ParticleFlyweight:
        key = (particle_type, texture, size, color)
        if key not in cls._flyweights:
            cls._flyweights[key] = ParticleFlyweight(
                particle_type, texture, size, color
            )
        cls._creation_count += 1
        return cls._flyweights[key]

    @classmethod
    def get_memory_stats(cls) -> dict:
        unique_flyweights = len(cls._flyweights)
        total_requests = cls._creation_count
        memory_saved = (1 - unique_flyweights / max(total_requests, 1)) * 100

        return {
            "unique_flyweights": unique_flyweights,
            "total_particle_requests": total_requests,
            "memory_saved_percentage": memory_saved,
            "reuse_ratio": total_requests / max(unique_flyweights, 1),
        }


class Particle:
    """Context class holding extrinsic state"""

    def __init__(self):
        self.flyweight: Optional[ParticleFlyweight] = None
        self.position: Tuple[float, float] = (0.0, 0.0)
        self.velocity: Tuple[float, float] = (0.0, 0.0)
        self.age: float = 0.0
        self.lifetime: float = 1.0
        self.is_alive: bool = False

    def initialize(
        self,
        flyweight: ParticleFlyweight,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
        lifetime: float,
    ) -> None:
        """Initialize or reinitialize this particle"""
        self.flyweight = flyweight
        self.position = position
        self.velocity = velocity
        self.age = 0.0
        self.lifetime = lifetime
        self.is_alive = True

    def update(self, delta_time: float) -> bool:
        """Update particle and return True if still alive"""
        if not self.is_alive:
            return False

        self.age += delta_time
        if self.age >= self.lifetime:
            self.is_alive = False
            return False

        # Update physics using flyweight
        self.position, self.velocity = self.flyweight.update_physics(
            self.position, self.velocity, delta_time
        )
        return True

    def render(self) -> None:
        if self.is_alive and self.flyweight:
            self.flyweight.render(self.position, self.velocity, self.age, self.lifetime)

    def reset(self) -> None:
        """Reset particle for object pooling"""
        self.is_alive = False
        self.flyweight = None


class ParticlePool:
    """Object pool for reusing Particle instances"""

    def __init__(self, initial_size: int = 1000):
        self._available: List[Particle] = [Particle() for _ in range(initial_size)]
        self._in_use: List[Particle] = []

    def acquire(
        self,
        flyweight: ParticleFlyweight,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
        lifetime: float,
    ) -> Particle:
        """Get a particle from the pool"""
        if self._available:
            particle = self._available.pop()
        else:
            # Pool exhausted, create new particle
            particle = Particle()

        particle.initialize(flyweight, position, velocity, lifetime)
        self._in_use.append(particle)
        return particle

    def release(self, particle: Particle) -> None:
        """Return a particle to the pool"""
        if particle in self._in_use:
            self._in_use.remove(particle)
            particle.reset()
            self._available.append(particle)

    def get_pool_stats(self) -> dict:
        return {
            "available": len(self._available),
            "in_use": len(self._in_use),
            "total_pool_size": len(self._available) + len(self._in_use),
        }


class ParticleSystem:
    def __init__(self, pool_size: int = 5000):
        self.particle_pool = ParticlePool(pool_size)
        self.active_particles: List[Particle] = []

    def spawn_explosion(
        self,
        position: Tuple[float, float],
        num_particles: int,
        particle_type: str = "explosion",
        texture: str = "explosion.png",
        size: float = 5.0,
        color: str = "orange",
    ) -> None:
        """Spawn an explosion effect"""
        flyweight = ParticleFactory.get_flyweight(particle_type, texture, size, color)

        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            velocity = (
                speed * math.cos(angle),
                speed * math.sin(angle),
            )
            lifetime = random.uniform(1.0, 3.0)

            particle = self.particle_pool.acquire(
                flyweight, position, velocity, lifetime
            )
            self.active_particles.append(particle)

    def spawn_smoke_trail(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        num_particles: int = 20,
    ) -> None:
        """Spawn a smoke trail between two points"""
        flyweight = ParticleFactory.get_flyweight("smoke", "smoke.png", 3.0, "gray")

        for i in range(num_particles):
            t = i / max(num_particles - 1, 1)
            position = (
                start_pos[0] + t * (end_pos[0] - start_pos[0]),
                start_pos[1] + t * (end_pos[1] - start_pos[1]),
            )
            velocity = (random.uniform(-10, 10), random.uniform(20, 40))
            lifetime = random.uniform(2.0, 4.0)

            particle = self.particle_pool.acquire(
                flyweight, position, velocity, lifetime
            )
            self.active_particles.append(particle)

    def update(self, delta_time: float) -> None:
        """Update all active particles"""
        particles_to_remove = []

        for particle in self.active_particles:
            if not particle.update(delta_time):
                particles_to_remove.append(particle)

        # Remove dead particles and return them to pool
        for particle in particles_to_remove:
            self.active_particles.remove(particle)
            self.particle_pool.release(particle)

    def render(self) -> None:
        """Render all active particles"""
        for particle in self.active_particles:
            particle.render()

    def get_system_stats(self) -> dict:
        """Get comprehensive system statistics"""
        return {
            "active_particles": len(self.active_particles),
            "pool_stats": self.particle_pool.get_pool_stats(),
            "flyweight_stats": ParticleFactory.get_memory_stats(),
        }


# Performance test and demonstration
if __name__ == "__main__":
    print("=== High-Performance Particle System Demo ===\n")

    particle_system = ParticleSystem(pool_size=10000)

    # Simulate multiple explosions
    print("Spawning multiple explosion effects...")
    particle_system.spawn_explosion((100, 100), 500, color="red")
    particle_system.spawn_explosion((200, 150), 300, color="blue")
    particle_system.spawn_explosion((150, 200), 400, color="green")

    # Add smoke trails
    particle_system.spawn_smoke_trail((0, 0), (100, 100), 50)
    particle_system.spawn_smoke_trail((200, 0), (200, 200), 75)

    print(f"\nInitial system stats:")
    stats = particle_system.get_system_stats()
    for category, data in stats.items():
        print(f"{category}: {data}")

    # Simulate several update cycles
    print(f"\nSimulating particle system updates...")
    for frame in range(5):
        particle_system.update(0.016)  # ~60 FPS
        current_stats = particle_system.get_system_stats()
        print(
            f"Frame {frame + 1}: {current_stats['active_particles']} active particles"
        )

    print(f"\nFinal system performance:")
    final_stats = particle_system.get_system_stats()
    flyweight_stats = final_stats["flyweight_stats"]

    print(f"Memory efficiency: {flyweight_stats['memory_saved_percentage']:.1f}% saved")
    print(f"Flyweight reuse ratio: {flyweight_stats['reuse_ratio']:.1f}x")
    print(f"Pool utilization: {final_stats['pool_stats']}")

    # Demonstrate that we can handle thousands of particles efficiently
    print(f"\n=== Stress Test: 5000 particles ===")
    particle_system.spawn_explosion((0, 0), 5000, color="yellow")
    stress_stats = particle_system.get_system_stats()
    print(f"Handling {stress_stats['active_particles']} particles efficiently!")
    print(f"Unique flyweights: {stress_stats['flyweight_stats']['unique_flyweights']}")
