#!/usr/bin/env python3
from __future__ import annotations

import time
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
class DirectionState:
    up_is_pressed: bool
    down_is_pressed: bool
    left_is_pressed: bool
    right_is_pressed: bool


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


def main() -> None:
    gpio_bcm_pin_by_direction: Dict[str, int] = {
        "up": 17,
        "left": 27,
        "down": 22,
        "right": 23,
    }

    polling_interval_seconds: float = 0.002  # 2 ms
    debounce_seconds: float = 0.01  # 10 ms

    debounced_input_by_direction: Dict[str, DebouncedInput] = {
        direction_name: DebouncedInput(gpio_bcm_pin, debounce_seconds)
        for direction_name, gpio_bcm_pin in gpio_bcm_pin_by_direction.items()
    }

    # Emular TECLADO: StepMania con InputDrivers=X11 lo toma seguro
    device_capabilities = {
        evdev_ecodes.EV_KEY: [
            evdev_ecodes.KEY_UP,
            evdev_ecodes.KEY_DOWN,
            evdev_ecodes.KEY_LEFT,
            evdev_ecodes.KEY_RIGHT,
        ],
    }

    previous_direction_state = DirectionState(
        up_is_pressed=False,
        down_is_pressed=False,
        left_is_pressed=False,
        right_is_pressed=False,
    )

    with UInput(
        events=device_capabilities,
        name="DDR GPIO Dance Pad (Keyboard)",
        bustype=evdev_ecodes.BUS_USB,
    ) as virtual_keyboard:
        print("Dispositivo virtual listo: 'DDR GPIO Dance Pad (Keyboard)'")
        print("GPIO:", gpio_bcm_pin_by_direction)
        print("Presiona Ctrl+C para salir.")

        while True:
            current_direction_state = DirectionState(
                up_is_pressed=debounced_input_by_direction[
                    "up"
                ].read_stable_is_pressed(),
                left_is_pressed=debounced_input_by_direction[
                    "left"
                ].read_stable_is_pressed(),
                down_is_pressed=debounced_input_by_direction[
                    "down"
                ].read_stable_is_pressed(),
                right_is_pressed=debounced_input_by_direction[
                    "right"
                ].read_stable_is_pressed(),
            )

            should_sync = False

            if (
                current_direction_state.up_is_pressed
                != previous_direction_state.up_is_pressed
            ):
                virtual_keyboard.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.KEY_UP,
                    int(current_direction_state.up_is_pressed),
                )
                should_sync = True

            if (
                current_direction_state.down_is_pressed
                != previous_direction_state.down_is_pressed
            ):
                virtual_keyboard.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.KEY_DOWN,
                    int(current_direction_state.down_is_pressed),
                )
                should_sync = True

            if (
                current_direction_state.left_is_pressed
                != previous_direction_state.left_is_pressed
            ):
                virtual_keyboard.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.KEY_LEFT,
                    int(current_direction_state.left_is_pressed),
                )
                should_sync = True

            if (
                current_direction_state.right_is_pressed
                != previous_direction_state.right_is_pressed
            ):
                virtual_keyboard.write(
                    evdev_ecodes.EV_KEY,
                    evdev_ecodes.KEY_RIGHT,
                    int(current_direction_state.right_is_pressed),
                )
                should_sync = True

            if should_sync:
                virtual_keyboard.syn()
                previous_direction_state = current_direction_state

            time.sleep(polling_interval_seconds)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaliendo.")
