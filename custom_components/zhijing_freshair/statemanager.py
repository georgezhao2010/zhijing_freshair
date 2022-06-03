import socket
import threading
import time
import logging
import binascii

from .const import (
    DEVICE_CLASS_PM25,
    DEVICE_CLASS_VOC,
    DEVICE_CLASS_FILTER,
    MODE_AUTO,
    MODE_MANUALLY,
    MODE_TIMING,
    SPEED_OFF,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_HIGH,
    ATTR_SPEED
)

from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    STATE_ON,
    STATE_OFF,
    ATTR_MODE,
    ATTR_STATE,
    ATTR_ICON
)

MSG_TYPE_GET_DATA = bytearray([0x31, 0x31, 0x30, 0x32])
MSG_TYPE_TURN_OFF = bytearray([0x32, 0x31, 0x30, 0x33])
MSG_TYPE_TURN_ON = bytearray([0x32, 0x31, 0x31, 0x34])
MSG_TYPE_SET_MODE_AUTO = bytearray([0x33, 0x31, 0x31, 0x35])
MSG_TYPE_SET_MODE_MANUALLY = bytearray([0x33, 0x31, 0x32, 0x36])
MSG_TYPE_SET_MODE_TIMING = bytearray([0x33, 0x31, 0x33, 0x37])
MSG_TYPE_SET_SPEED_OFF = bytearray([0x35, 0x31, 0x30, 0x36])
MSG_TYPE_SET_SPEED_LOW = bytearray([0x35, 0x31, 0x31, 0x37])
MSG_TYPE_SET_SPEED_MEDIUM = bytearray([0x35, 0x31, 0x32, 0x38])
MSG_TYPE_SET_SPEED_HIGH = bytearray([0x35, 0x31, 0x33, 0x39])

ICON_ON = "mdi:fan"
ICON_OFF = "mdi:fan-off"

_LOGGER = logging.getLogger(__name__)


class DeviceMessage:
    def __init__(self):
        self._message = bytearray([
            # 包头
            0x30, 0x68,
            # 长度
            0x00, 0x00,
            # 间隔
            0x00, 0x00, 0x00, 0x00,
            # 管他是什么
            0x55, 0x30, 0x30, 0x73, 0x30, 0x30, 0x30, 0x31, 0x30, 0x30, 0x30, 0x30, 0x73, 0x5f, 0x54, 0x55,
            0x7e, 0x51, 0x5d, 0x55, 0x0d, 0x77, 0x55, 0x44, 0x65, 0x51, 0x42, 0x44, 0x74, 0x51, 0x44, 0x51,
            0x16, 0x73, 0x58, 0x5e, 0x0d, 0x00, 0x16, 0x7c, 0x55, 0x5e, 0x0d, 0x07, 0x16, 0x65, 0x43, 0x55,
            0x42, 0x72, 0x59, 0x5e, 0x51, 0x42, 0x49, 0x74, 0x51, 0x44, 0x51, 0x0d, 0xc1, 0xc1,
            # 命令
            0x00, 0x00, 0x00, 0x00,
            # 结束
            0x4e
        ])

    def build(self, message_type):
        msg_len = len(self._message)
        self._message[2:4] = msg_len.to_bytes(2, 'big')
        self._message[msg_len - 5: msg_len - 1] = message_type
        return self._message


def byte_co_decode(byte):
    if (byte & 0x30) == 0x30:
        byte = byte - 0x30
    elif (byte & 0x20) == 0x20:
        byte = byte - 0x10
    elif (byte & 0x10) == 0x10:
        byte = byte + 0x10
    else:
        byte = byte + 0x30
    return byte


class Timer(threading.Thread):
    def __init__(self, interval, function):
        threading.Thread.__init__(self)
        self._intreval = interval
        self._function = function
        self._finished = threading.Event()

    def cancel(self):
        self._finished.set()

    def run(self):
        while not self._finished.is_set():
            self._finished.wait(self._intreval)
            if not self._finished.is_set():
                self._function()
        self._finished.set()


class DeviceInterface(threading.Thread):
    def __init__(self, host, port, on_fan_state_changed, on_sensor_state_changed):
        threading.Thread.__init__(self)
        self._lock = threading.Lock()
        self._socket = None
        self._host = host
        self._port = port
        self._on_fan_state_changed = on_fan_state_changed
        self._on_sensor_state_changed = on_sensor_state_changed
        self._is_run = False
        self._is_on = None
        self._mode = None
        self._speed = None
        self._pm_25 = None
        self._voc = None
        self._temperature = None
        self._humidity = None
        self._filter = None
        self._timer = None
        request = DeviceMessage()
        self._get_data = request.build(MSG_TYPE_GET_DATA)

    def open(self, start_thread):
        with self._lock:
            if self._socket is None:
                try:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.settimeout(3)
                    self._socket.connect((self._host, self._port))
                    self._timer = Timer(5, self.send_timer)
                    self._timer.start()
                    result = True
                except socket.timeout:
                    result = False
                except socket.error:
                    result = False
            else:
                result = True
            if start_thread:
                self._is_run = True
                threading.Thread.start(self)
        return result

    def close(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            if self._socket is not None:
                if self._is_run:
                    self._is_run = False
                self._socket.close()
                self._socket = None

    def send(self, msg):
        _LOGGER.debug(f"Send {binascii.hexlify(msg)}")
        with self._lock:
            try:
                self._socket.send(msg)
            except socket.timeout:
                pass
            except socket.error:
                pass

    def set_mode(self, mode):
        request = DeviceMessage()
        msg = None
        if mode == MODE_AUTO:
            msg = request.build(MSG_TYPE_SET_MODE_AUTO)
        elif mode == MODE_MANUALLY:
            msg = request.build(MSG_TYPE_SET_MODE_MANUALLY)
        elif mode == MODE_TIMING:
            msg = request.build(MSG_TYPE_SET_MODE_TIMING)
        if msg is not None:
            self.send(msg)

    def set_speed(self, speed):
        request = DeviceMessage()
        msg = None
        if speed == SPEED_OFF:
            msg = request.build(MSG_TYPE_SET_SPEED_OFF)
        elif speed == SPEED_LOW:
            msg = request.build(MSG_TYPE_SET_SPEED_LOW)
        elif speed == SPEED_MEDIUM:
            msg = request.build(MSG_TYPE_SET_SPEED_MEDIUM)
        elif speed == SPEED_HIGH:
            msg = request.build(MSG_TYPE_SET_SPEED_HIGH)
        if msg is not None:
            self.send(msg)

    def turn_on(self):
        request = DeviceMessage()
        msg = request.build(MSG_TYPE_TURN_ON)
        self.send(msg)

    def turn_off(self):
        request = DeviceMessage()
        msg = request.build(MSG_TYPE_TURN_OFF)
        self.send(msg)

    def read_state_message(self, msg):
        # get fan states
        is_on = STATE_ON if byte_co_decode(msg[76]) == 1 else STATE_OFF
        icon = ICON_ON if is_on == STATE_ON else ICON_OFF
        mode = byte_co_decode(msg[77])
        if mode == 1:
            mode = MODE_AUTO
        elif mode == 2:
            mode = MODE_MANUALLY
        else:
            mode = MODE_TIMING

        speed = byte_co_decode(msg[78])
        if speed == 0:
            speed = SPEED_OFF
        elif speed == 1:
            speed = SPEED_LOW
        elif speed == 2:
            speed = SPEED_MEDIUM
        else:
            speed = SPEED_HIGH
        # get sensor states
        temperature = byte_co_decode(msg[86])
        humidity = byte_co_decode(msg[87])
        pm2_5 = (byte_co_decode(msg[88]) << 8) + byte_co_decode(msg[89])
        voc = byte_co_decode(msg[93]) / 10
        filter_state = byte_co_decode(msg[94])

        fan_state = {}
        sensor_state = {}

        if is_on != self._is_on:
            fan_state[ATTR_ICON] = icon
            fan_state[ATTR_STATE] = self._is_on = is_on
        if mode != self._mode:
            fan_state[ATTR_MODE] = self._mode = mode
        if speed != self._speed:
            fan_state[ATTR_SPEED] = self._speed = speed
        if temperature != self._temperature:
            sensor_state[DEVICE_CLASS_TEMPERATURE] = self._temperature = temperature

        if humidity != self._humidity:
            sensor_state[DEVICE_CLASS_HUMIDITY] = self._humidity = humidity
        if pm2_5 != self._pm_25:
            sensor_state[DEVICE_CLASS_PM25] = self._pm_25 = pm2_5
        if voc != self._voc:
            sensor_state[DEVICE_CLASS_VOC] = self._voc = voc
        if filter_state != self._filter:
            sensor_state[DEVICE_CLASS_FILTER] = self._filter = filter_state

        return fan_state, sensor_state

    def send_timer(self):
        self.send(self._get_data)

    def run(self):
        while self._is_run:
            with self._lock:
                while self._socket is None:
                    try:
                        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self._socket.settimeout(5)
                        self._socket.connect((self._host, self._port))
                    except socket.timeout:
                        self._socket.close()
                        self._socket = None
                        time.sleep(3)
                    except socket.error:
                        self._socket.close()
                        self._socket = None
                        time.sleep(3)
                    if not self._is_run:
                        self._socket.close()
                        self._socket = None
                        return
            while self._is_run:
                try:
                    msg = self._socket.recv(1024)
                    _LOGGER.debug(f"Received {binascii.hexlify(msg)}")
                    if not self._is_run:
                        break
                    msg_len = len(msg)
                    if msg_len == 0:
                        raise socket.error
                    if msg_len == 97:  # 本地数据上报应有长度
                        fan_state, sensor_state = self.read_state_message(msg)
                        _LOGGER.debug(f"fan_state = {fan_state}, sensor_state = {sensor_state}")
                        if len(fan_state) > 0:
                            if not self._on_fan_state_changed(fan_state):
                                self._is_on = None
                                self._mode = None
                                self._speed = None
                        if len(sensor_state) > 0:
                            if not self._on_sensor_state_changed(sensor_state):
                                self._pm_25 = None
                                self._voc = None
                                self._temperature = None
                                self._humidity = None
                                self._filter = None
                except socket.timeout:
                    pass
                except socket.error:
                    _LOGGER.debug(f"Except socket.error {socket.error.errno} raised in socket.recv()")
                    with self._lock:
                        self._socket.close()
                        self._socket = None
                        break


class StateManager:
    def __init__(self, host, port):
        self._device = DeviceInterface(host, port, self.on_fan_state_changed, self.on_sensor_state_changed)
        self._sensor_updates = {}
        self._fan_update = None

    def add_sensor_update(self, sensor_type, handler):
        self._sensor_updates[sensor_type] = handler

    def set_fan_update(self, handler):
        self._fan_update = handler

    def on_fan_state_changed(self, fan_state):
        if self._fan_update is not None:
            self._fan_update(fan_state)
            return True
        else:
            return False

    def on_sensor_state_changed(self, sensor_state):
        result = True
        for sensor_type in sensor_state:
            if sensor_type in self._sensor_updates:
                self._sensor_updates[sensor_type](sensor_state[sensor_type])
            else:
                result = False
        return result

    def open(self):
        self._device.open(True)

    async def async_open(self):
        pass

    def close(self):
        self._device.close()

    def turn_on(self):
        self._device.turn_on()

    def turn_off(self):
        self._device.turn_off()

    def set_mode(self, mode):
        self._device.set_mode(mode)

    def set_speed(self, speed):
        self._device.set_speed(speed)
