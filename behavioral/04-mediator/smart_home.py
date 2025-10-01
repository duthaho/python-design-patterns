from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class DeviceType(Enum):
    MOTION_SENSOR = "motion_sensor"
    LIGHT = "light"
    THERMOSTAT = "thermostat"
    ALARM = "alarm"


class SmartHomeHub:
    """Mediator for smart home devices"""

    def __init__(self) -> None:
        self.devices: dict[DeviceType, list["SmartDevice"]] = {}

    def register_device(self, device: "SmartDevice") -> None:
        device_type = device.device_type
        if device_type not in self.devices:
            self.devices[device_type] = []
        self.devices[device_type].append(device)
        print(f"[Hub] Registered {device}")

    def notify(self, sender: "SmartDevice", event: str, data: dict) -> None:
        """Central coordination logic based on events and device states"""

        if event == "motion_detected":
            hour = data.get("hour", datetime.now().hour)
            self._handle_motion(hour)

        elif event == "alarm_armed":
            self._handle_alarm_armed()

        elif event == "alarm_disarmed":
            print(f"[Hub] Alarm disarmed, resuming normal operation")

    def _handle_motion(self, hour: int) -> None:
        """Handle motion detection based on context"""
        alarm_armed = self._is_alarm_armed()

        if alarm_armed:
            print(f"[Hub] ⚠️  Motion detected while alarm is armed - INTRUSION!")
            self._trigger_intrusion_mode()
        elif self._is_night_time(hour):
            print(f"[Hub] Motion detected at night ({hour}:00)")
            self._activate_night_mode()
        else:
            print(f"[Hub] Motion detected during day")
            self._turn_on_lights(brightness=50)

    def _handle_alarm_armed(self) -> None:
        """Handle leaving home scenario"""
        print(f"[Hub] Leaving home mode activated")
        self._turn_off_all_lights()
        self._set_thermostats_eco_mode()

    def _is_alarm_armed(self) -> bool:
        """Query alarm state without direct reference"""
        alarms = self.devices.get(DeviceType.ALARM, [])
        return any(alarm.is_armed for alarm in alarms)

    def _is_night_time(self, hour: int) -> bool:
        return hour >= 22 or hour < 6

    def _trigger_intrusion_mode(self) -> None:
        """Intrusion response: trigger alarm, full brightness lights"""
        for alarm in self.devices.get(DeviceType.ALARM, []):
            alarm.trigger()
        self._turn_on_lights(brightness=100)

    def _activate_night_mode(self) -> None:
        """Night mode: low brightness lights"""
        self._turn_on_lights(brightness=30)

    def _turn_on_lights(self, brightness: int) -> None:
        for light in self.devices.get(DeviceType.LIGHT, []):
            light.set_brightness(brightness)

    def _turn_off_all_lights(self) -> None:
        for light in self.devices.get(DeviceType.LIGHT, []):
            light.turn_off()

    def _set_thermostats_eco_mode(self) -> None:
        for thermostat in self.devices.get(DeviceType.THERMOSTAT, []):
            thermostat.set_eco_mode(True)

    def get_device_state(self, device_type: DeviceType):
        """Allow devices to query others' states"""
        return [device.get_state() for device in self.devices.get(device_type, [])]


class SmartDevice(ABC):
    """Abstract colleague"""

    def __init__(self, name: str, hub: SmartHomeHub, device_type: DeviceType) -> None:
        self.name = name
        self.hub = hub
        self.device_type = device_type
        self.hub.register_device(self)  # Auto-register

    @abstractmethod
    def get_state(self) -> dict:
        """Return current device state"""
        pass

    def __str__(self) -> str:
        return f"{self.name}"


class MotionSensor(SmartDevice):
    def __init__(self, name: str, hub: SmartHomeHub):
        super().__init__(name, hub, DeviceType.MOTION_SENSOR)
        self.motion_detected = False

    def detect_motion(self, hour: int = None) -> None:
        if hour is None:
            hour = datetime.now().hour

        self.motion_detected = True
        print(f"\n[{self}] 🚶 Motion detected!")
        self.hub.notify(self, "motion_detected", {"hour": hour})

    def get_state(self) -> dict:
        return {"motion_detected": self.motion_detected}


class SmartLight(SmartDevice):
    def __init__(self, name: str, hub: SmartHomeHub):
        super().__init__(name, hub, DeviceType.LIGHT)
        self.is_on = False
        self.brightness = 0

    def set_brightness(self, brightness: int) -> None:
        self.is_on = True
        self.brightness = brightness
        print(f"[{self}] 💡 Light turned ON at {brightness}% brightness")

    def turn_off(self) -> None:
        self.is_on = False
        self.brightness = 0
        print(f"[{self}] 🌑 Light turned OFF")

    def get_state(self) -> dict:
        return {"is_on": self.is_on, "brightness": self.brightness}


class Thermostat(SmartDevice):
    def __init__(self, name: str, hub: SmartHomeHub):
        super().__init__(name, hub, DeviceType.THERMOSTAT)
        self.temperature = 22
        self.eco_mode = False

    def set_temperature(self, temp: int) -> None:
        self.temperature = temp
        print(f"[{self}] 🌡️  Temperature set to {temp}°C")

    def set_eco_mode(self, enabled: bool) -> None:
        self.eco_mode = enabled
        mode_str = "ENABLED" if enabled else "DISABLED"
        print(f"[{self}] 🌿 Eco mode {mode_str}")

    def get_state(self) -> dict:
        return {"temperature": self.temperature, "eco_mode": self.eco_mode}


class SecurityAlarm(SmartDevice):
    def __init__(self, name: str, hub: SmartHomeHub):
        super().__init__(name, hub, DeviceType.ALARM)
        self.is_armed = False
        self.is_triggered = False

    def arm(self) -> None:
        self.is_armed = True
        self.is_triggered = False
        print(f"\n[{self}] 🔒 Alarm ARMED")
        self.hub.notify(self, "alarm_armed", {})

    def disarm(self) -> None:
        self.is_armed = False
        self.is_triggered = False
        print(f"[{self}] 🔓 Alarm disarmed")
        self.hub.notify(self, "alarm_disarmed", {})

    def trigger(self) -> None:
        if self.is_armed:
            self.is_triggered = True
            print(f"[{self}] 🚨 ALARM TRIGGERED! INTRUDER ALERT!")

    def get_state(self) -> dict:
        return {"is_armed": self.is_armed, "is_triggered": self.is_triggered}


# Test scenarios
if __name__ == "__main__":
    hub = SmartHomeHub()

    motion_sensor = MotionSensor("Living Room Sensor", hub)
    living_light = SmartLight("Living Room Light", hub)
    thermostat = Thermostat("Main Thermostat", hub)
    alarm = SecurityAlarm("Home Alarm", hub)

    # Scenario 1: Motion at night
    print("\n" + "=" * 50)
    print("SCENARIO 1: Motion detected at night")
    print("=" * 50)
    motion_sensor.detect_motion(hour=22)

    # Scenario 2: Arm alarm and detect motion (intrusion)
    print("\n" + "=" * 50)
    print("SCENARIO 2: Armed alarm with motion (INTRUSION)")
    print("=" * 50)
    alarm.arm()
    motion_sensor.detect_motion(hour=14)

    # Scenario 3: Disarm and detect daytime motion
    print("\n" + "=" * 50)
    print("SCENARIO 3: Normal daytime motion")
    print("=" * 50)
    alarm.disarm()
    motion_sensor.detect_motion(hour=14)
