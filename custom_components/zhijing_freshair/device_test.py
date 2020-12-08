from statemanager import (
    StateManager,
    MODE_AUTO,
    MODE_MANUALLY,
    MODE_TIMING,
    SPEED_OFF,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_HIGH
)
import time


device = StateManager("192.168.1.126", 9600)

tests = {
    "opening the device": {"function": device.open},
    "turn off the device": {"function": device.turn_off},
    "turn on the device": {"function": device.turn_on},
    "set the device speed off": {"function": device.set_speed, "param": SPEED_OFF},
    "set the device speed low": {"function": device.set_speed, "param": SPEED_LOW},
    "set the device speed medium": {"function": device.set_speed, "param": SPEED_MEDIUM},
    "set the device speed high": {"function": device.set_speed, "param": SPEED_HIGH},
    "set the device mode timing": {"function": device.set_mode, "param": MODE_TIMING},
    "set the device mode auto": {"function": device.set_mode, "param": MODE_AUTO},
    "set the device mode manually": {"function": device.set_mode, "param": MODE_MANUALLY},
    "closing the device": {"function": device.close}
}

print("test begin")
for test in tests:
    print(test)
    tests[test]["function"](tests[test]["param"]) if "param" in tests[test] else tests[test]["function"]()
    time.sleep(3)
print("test complete")
