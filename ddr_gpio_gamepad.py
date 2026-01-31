#!/usr/bin/env python3
from __future__ import annotations

import time
from evdev import AbsInfo
from dataclasses import dataclass
from typing import Dict

from evdev import UInput, ecodes as evdev_ecodes

try:
    from gpiozero import Button
except ImportError as import_error:
    raise SystemExit(
        "Falta gpiozero. Instala con: sudo apt install -y python3-gpiozero"
    ) from import_error


@dataclass(frozen=True)
class DpadState:
    hat_x: int  # -1 izquierda, 0 centro, +1 derecha
    hat_y: int  # -1 arriba, 0 centro, +1 abajo


class DebouncedInput:
    """
    Mantiene estado estable con debounce por tiempo.
    Entradas activas en LOW (pull-up interno), típico de botón a GND.
    """

    def __init__(self, gpio_bcm_pin: int, debounce_seconds: float) -> None:
        self._button = Button(gpio_bcm_pin, pull_up=True, bounce_time=None)
        self._debounce_seconds = debounce_seconds
        self._last_raw_is_pressed = self._button.is_pressed
        self._stable_is_pressed = self._last_raw_is_pressed
        self._last_change_timestamp = time.monotonic()

    def read_stable_is_pressed(self) -> bool:
        current_raw_is_pressed = self._button.is_pressed
        current_timestamp = time.monotonic()

        if current_raw_is_pressed != self._last_raw_is_pressed:
            self._last_raw_is_pressed = current_raw_is_pressed
            self._last_change_timestamp = current_timestamp

        if current_timestamp - self._last_change_timestamp >= self._debounce_seconds:
            self._stable_is_pressed = self._last_raw_is_pressed

        return self._stable_is_pressed


def clamp_hat_value(value: int) -> int:
    if value < -1:
        return -1
    if value > 1:
        return 1
    return value


def compute_dpad_hat(
    up_is_pressed: bool,
    down_is_pressed: bool,
    left_is_pressed: bool,
    right_is_pressed: bool,
) -> DpadState:
    # Eje X: izquierda (-1) / derecha (+1)
    hat_x = 0
    if left_is_pressed and not right_is_pressed:
        hat_x = -1
    elif right_is_pressed and not left_is_pressed:
        hat_x = 1

    # Eje Y: arriba (-1) / abajo (+1)
    hat_y = 0
    if up_is_pressed and not down_is_pressed:
        hat_y = -1
    elif down_is_pressed and not up_is_pressed:
        hat_y = 1

    return DpadState(hat_x=hat_x, hat_y=hat_y)


def main() -> None:
    # ====== Configuración GPIO (BCM) ======
    gpio_bcm_pin_by_direction: Dict[str, int] = {
        "up": 17,
        "left": 27,
        "down": 22,
        "right": 23,
    }

    # ====== Ajustes finos ======
    polling_interval_seconds: float = 0.002  # 2 ms (baja latencia)
    debounce_seconds: float = 0.01  # 10 ms (ajustable)

    # ====== Preparar inputs con debounce ======
    debounced_input_by_direction: Dict[str, DebouncedInput] = {
        direction_name: DebouncedInput(gpio_bcm_pin, debounce_seconds)
        for direction_name, gpio_bcm_pin in gpio_bcm_pin_by_direction.items()
    }

    # ====== Crear gamepad virtual (uinput) ======
    device_capabilities = {
        evdev_ecodes.EV_KEY: [
            evdev_ecodes.BTN_DPAD_UP,
            evdev_ecodes.BTN_DPAD_DOWN,
            evdev_ecodes.BTN_DPAD_LEFT,
            evdev_ecodes.BTN_DPAD_RIGHT,
        ],
        evdev_ecodes.EV_ABS: [
            (
                evdev_ecodes.ABS_HAT0X,
                AbsInfo(
                    value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0
                ),  # min, max, fuzz, flat
            ),
            (
                evdev_ecodes.ABS_HAT0Y,
                AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0),
            ),
        ],
    }

    with UInput(
        events=device_capabilities,
        name="DDR GPIO Dance Pad",
        bustype=evdev_ecodes.BUS_USB,
    ) as virtual_gamepad:
        print("Gamepad virtual listo: 'DDR GPIO Dance Pad'")
        print("GPIO:", gpio_bcm_pin_by_direction)
        print("Presiona Ctrl+C para salir.")

        previous_dpad_state = DpadState(hat_x=0, hat_y=0)

        previous_up_is_pressed = False
        previous_down_is_pressed = False
        previous_left_is_pressed = False
        previous_right_is_pressed = False

        while True:
            up_is_pressed = debounced_input_by_direction["up"].read_stable_is_pressed()
            left_is_pressed = debounced_input_by_direction[
                "left"
            ].read_stable_is_pressed()
            down_is_pressed = debounced_input_by_direction[
                "down"
            ].read_stable_is_pressed()
            right_is_pressed = debounced_input_by_direction[
                "right"
            ].read_stable_is_pressed()

            current_dpad_state = compute_dpad_hat(
                up_is_pressed=up_is_pressed,
                down_is_pressed=down_is_pressed,
                left_is_pressed=left_is_pressed,
                right_is_pressed=right_is_pressed,
            )

            should_sync = False

            # ====== Emitir botones (EV_KEY) ======
            if up_is_pressed != previous_up_is_pressed:
                virtual_gamepad.write(
                    evdev_ecodes.EV_KEY, evdev_ecodes.BTN_DPAD_UP, int(up_is_pressed)
                )
                previous_up_is_pressed = up_is_pressed
                should_sync = True

            if down_is_pressed != previous_down_is_pressed:
                virtual_gamepad.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.BTN_DPAD_DOWN,
                    int(down_is_pressed),
                )
                previous_down_is_pressed = down_is_pressed
                should_sync = True

            if left_is_pressed != previous_left_is_pressed:
                virtual_gamepad.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.BTN_DPAD_LEFT,
                    int(left_is_pressed),
                )
                previous_left_is_pressed = left_is_pressed
                should_sync = True

            if right_is_pressed != previous_right_is_pressed:
                virtual_gamepad.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.BTN_DPAD_RIGHT,
                    int(right_is_pressed),
                )
                previous_right_is_pressed = right_is_pressed
                should_sync = True

            # ====== Emitir HAT (EV_ABS) ======
            if current_dpad_state.hat_x != previous_dpad_state.hat_x:
                virtual_gamepad.write(
                    evdev_ecodes.EV_ABS,
                    evdev_ecodes.ABS_HAT0X,
                    clamp_hat_value(current_dpad_state.hat_x),
                )
                should_sync = True

            if current_dpad_state.hat_y != previous_dpad_state.hat_y:
                virtual_gamepad.write(
                    evdev_ecodes.EV_ABS,
                    evdev_ecodes.ABS_HAT0Y,
                    clamp_hat_value(current_dpad_state.hat_y),
                )
                should_sync = True

            if should_sync:
                virtual_gamepad.syn()
                previous_dpad_state = current_dpad_state

            time.sleep(polling_interval_seconds)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaliendo.")
