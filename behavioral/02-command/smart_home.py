import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

# ============================================================================
# RECEIVERS - Smart Home Devices
# ============================================================================


class Light:
    def __init__(self, name: str):
        self.name = name
        self._is_on = False
        self._brightness = 100

    def turn_on(self):
        self._is_on = True
        print(f"[{self.name}] Light turned ON")

    def turn_off(self):
        self._is_on = False
        print(f"[{self.name}] Light turned OFF")

    def dim(self, level: int):
        if not self._is_on:
            print(f"[{self.name}] Cannot dim - light is OFF")
            return
        self._brightness = max(0, min(100, level))
        print(f"[{self.name}] Light dimmed to {self._brightness}%")

    def get_state(self) -> Dict[str, Any]:
        return {"is_on": self._is_on, "brightness": self._brightness}

    def set_state(self, state: Dict[str, Any]):
        self._is_on = state["is_on"]
        self._brightness = state["brightness"]


class Thermostat:
    def __init__(self, name: str):
        self.name = name
        self._temperature = 20

    def set_temperature(self, temp: int):
        self._temperature = temp
        print(f"[{self.name}] Temperature set to {self._temperature}°C")

    def get_state(self) -> Dict[str, Any]:
        return {"temperature": self._temperature}

    def set_state(self, state: Dict[str, Any]):
        self._temperature = state["temperature"]


class SecuritySystem:
    def __init__(self, name: str):
        self.name = name
        self._is_armed = False

    def arm(self):
        self._is_armed = True
        print(f"[{self.name}] Security system ARMED")

    def disarm(self):
        self._is_armed = False
        print(f"[{self.name}] Security system DISARMED")

    def get_state(self) -> Dict[str, Any]:
        return {"is_armed": self._is_armed}

    def set_state(self, state: Dict[str, Any]):
        self._is_armed = state["is_armed"]


# ============================================================================
# COMMAND INTERFACE
# ============================================================================


class Command(ABC):
    def __init__(self):
        self.timestamp: Optional[datetime] = None
        self.executed = False

    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if successful."""
        pass

    @abstractmethod
    def undo(self):
        """Undo the command."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize command to dictionary for persistence."""
        return {
            "command_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "executed": self.executed,
        }

    def __str__(self) -> str:
        time_str = (
            self.timestamp.strftime("%H:%M:%S") if self.timestamp else "Not executed"
        )
        return f"{self.__class__.__name__} ({time_str})"


# ============================================================================
# CONCRETE COMMANDS - Light Controls
# ============================================================================


class TurnOnLightCommand(Command):
    def __init__(self, light: Light):
        super().__init__()
        self._light = light
        self._prev_state: Optional[Dict] = None

    def execute(self) -> bool:
        self._prev_state = self._light.get_state()
        self._light.turn_on()
        self.timestamp = datetime.now()
        self.executed = True
        return True

    def undo(self):
        if self._prev_state:
            self._light.set_state(self._prev_state)
            print(f"[{self._light.name}] State restored")


class TurnOffLightCommand(Command):
    def __init__(self, light: Light):
        super().__init__()
        self._light = light
        self._prev_state: Optional[Dict] = None

    def execute(self) -> bool:
        self._prev_state = self._light.get_state()
        self._light.turn_off()
        self.timestamp = datetime.now()
        self.executed = True
        return True

    def undo(self):
        if self._prev_state:
            self._light.set_state(self._prev_state)
            print(f"[{self._light.name}] State restored")


class DimLightCommand(Command):
    def __init__(self, light: Light, level: int):
        super().__init__()
        self._light = light
        self._level = level
        self._prev_state: Optional[Dict] = None

    def execute(self) -> bool:
        self._prev_state = self._light.get_state()
        self._light.dim(self._level)
        self.timestamp = datetime.now()
        self.executed = True
        return True

    def undo(self):
        if self._prev_state:
            self._light.set_state(self._prev_state)
            print(
                f"[{self._light.name}] Brightness restored to {self._prev_state['brightness']}%"
            )


# ============================================================================
# CONCRETE COMMANDS - Thermostat Controls
# ============================================================================


class SetTemperatureCommand(Command):
    def __init__(self, thermostat: Thermostat, temp: int):
        super().__init__()
        self._thermostat = thermostat
        self._temp = temp
        self._prev_state: Optional[Dict] = None

    def execute(self) -> bool:
        self._prev_state = self._thermostat.get_state()
        self._thermostat.set_temperature(self._temp)
        self.timestamp = datetime.now()
        self.executed = True
        return True

    def undo(self):
        if self._prev_state:
            self._thermostat.set_state(self._prev_state)
            print(
                f"[{self._thermostat.name}] Temperature restored to {self._prev_state['temperature']}°C"
            )


# ============================================================================
# CONCRETE COMMANDS - Security Controls
# ============================================================================


class ArmSecurityCommand(Command):
    def __init__(self, security: SecuritySystem):
        super().__init__()
        self._security = security
        self._prev_state: Optional[Dict] = None

    def execute(self) -> bool:
        self._prev_state = self._security.get_state()
        self._security.arm()
        self.timestamp = datetime.now()
        self.executed = True
        return True

    def undo(self):
        if self._prev_state:
            self._security.set_state(self._prev_state)
            print(f"[{self._security.name}] Security state restored")


class DisarmSecurityCommand(Command):
    def __init__(self, security: SecuritySystem):
        super().__init__()
        self._security = security
        self._prev_state: Optional[Dict] = None

    def execute(self) -> bool:
        self._prev_state = self._security.get_state()
        self._security.disarm()
        self.timestamp = datetime.now()
        self.executed = True
        return True

    def undo(self):
        if self._prev_state:
            self._security.set_state(self._prev_state)
            print(f"[{self._security.name}] Security state restored")


# ============================================================================
# MACRO COMMANDS - Scenes
# ============================================================================


class SceneCommand(Command):
    """Execute multiple commands as a single scene"""

    def __init__(self, name: str, commands: List[Command]):
        super().__init__()
        self.name = name
        self._commands = commands

    def execute(self) -> bool:
        print(f"\n{'='*50}")
        print(f"Activating Scene: {self.name}")
        print(f"{'='*50}")

        for cmd in self._commands:
            cmd.execute()

        self.timestamp = datetime.now()
        self.executed = True
        print(f"{'='*50}\n")
        return True

    def undo(self):
        print(f"\nDeactivating Scene: {self.name}")
        for cmd in reversed(self._commands):
            cmd.undo()

    def __str__(self) -> str:
        time_str = (
            self.timestamp.strftime("%H:%M:%S") if self.timestamp else "Not executed"
        )
        return f"Scene '{self.name}' with {len(self._commands)} commands ({time_str})"


# ============================================================================
# SCHEDULED COMMAND DECORATOR
# ============================================================================


class ScheduledCommand(Command):
    """Decorator that adds delay to any command"""

    def __init__(self, command: Command, delay_seconds: int):
        super().__init__()
        self._command = command
        self._delay = delay_seconds

    def execute(self) -> bool:
        print(f"⏰ Scheduling command for {self._delay} seconds from now...")
        time.sleep(self._delay)
        result = self._command.execute()
        self.timestamp = datetime.now()
        self.executed = result
        return result

    def undo(self):
        if not self.executed:
            print("⚠️ Cannot undo: scheduled command never executed")
            return
        self._command.undo()

    def __str__(self) -> str:
        return f"Scheduled({self._delay}s): {self._command}"


# ============================================================================
# INVOKER - Remote Control with History
# ============================================================================


class RemoteControl:
    def __init__(self):
        self._buttons: Dict[str, Command] = {}
        self._history: List[Command] = []
        self._redo_stack: List[Command] = []

    def set_button(self, button_name: str, command: Command):
        """Assign a command to a button"""
        self._buttons[button_name] = command
        print(f"✓ Button '{button_name}' configured: {command.__class__.__name__}")

    def press_button(self, button_name: str):
        """Execute command assigned to button"""
        if button_name not in self._buttons:
            print(f"❌ No command assigned to button '{button_name}'")
            return

        command = self._buttons[button_name]
        if command.execute():
            self._history.append(command)
            self._redo_stack.clear()  # Clear redo stack on new action
            print(f"✓ Button '{button_name}' pressed\n")

    def undo(self):
        """Undo last executed command"""
        if not self._history:
            print("❌ Nothing to undo")
            return

        command = self._history.pop()
        command.undo()
        self._redo_stack.append(command)
        print(f"⟲ Undone: {command}\n")

    def redo(self):
        """Redo last undone command"""
        if not self._redo_stack:
            print("❌ Nothing to redo")
            return

        command = self._redo_stack.pop()
        command.execute()
        self._history.append(command)
        print(f"⟳ Redone: {command}\n")

    def show_history(self):
        """Display command history"""
        print("\n" + "=" * 60)
        print("COMMAND HISTORY")
        print("=" * 60)
        if not self._history:
            print("No commands executed yet")
        else:
            for i, cmd in enumerate(self._history, 1):
                print(f"{i}. {cmd}")
        print("=" * 60 + "\n")

    def save_history(self, filename: str):
        """Save command history to JSON file"""
        data = {
            "commands": [cmd.to_dict() for cmd in self._history],
            "saved_at": datetime.now().isoformat(),
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✓ History saved to {filename}")

    def clear_history(self):
        """Clear command history"""
        self._history.clear()
        self._redo_stack.clear()
        print("✓ History cleared")


# ============================================================================
# CLIENT CODE - Demo
# ============================================================================


def main():
    # Initialize devices
    living_room_light = Light("Living Room")
    bedroom_light = Light("Bedroom")
    thermostat = Thermostat("Main Floor")
    security = SecuritySystem("Home Security")

    # Initialize remote control
    remote = RemoteControl()

    # Configure buttons
    remote.set_button("living_on", TurnOnLightCommand(living_room_light))
    remote.set_button("living_off", TurnOffLightCommand(living_room_light))
    remote.set_button("living_dim", DimLightCommand(living_room_light, 30))
    remote.set_button("temp_22", SetTemperatureCommand(thermostat, 22))
    remote.set_button("arm", ArmSecurityCommand(security))

    print("\n" + "=" * 60)
    print("SMART HOME DEMO")
    print("=" * 60 + "\n")

    # Test basic operations
    print("--- Basic Operations ---")
    remote.press_button("living_on")
    remote.press_button("living_dim")
    remote.press_button("temp_22")
    remote.press_button("arm")

    # Show history
    remote.show_history()

    # Test undo/redo
    print("--- Testing Undo ---")
    remote.undo()
    remote.undo()

    print("\n--- Testing Redo ---")
    remote.redo()

    # Create a scene (Movie Mode)
    print("\n--- Testing Scene Command ---")
    movie_mode = SceneCommand(
        "Movie Mode",
        [
            DimLightCommand(living_room_light, 20),
            TurnOffLightCommand(bedroom_light),
            SetTemperatureCommand(thermostat, 21),
        ],
    )
    remote.set_button("movie", movie_mode)
    remote.press_button("movie")

    # Test scheduled command
    print("\n--- Testing Scheduled Command ---")
    scheduled = ScheduledCommand(
        TurnOffLightCommand(living_room_light), delay_seconds=2
    )
    remote.set_button("auto_off", scheduled)
    remote.press_button("auto_off")

    # Final history
    remote.show_history()

    # Save history
    remote.save_history("smart_home_history.json")
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
