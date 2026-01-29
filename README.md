# DDR Controller (GPIO -> Gamepad)

Convierte un pad DDR conectado a los GPIO de una Raspberry Pi en un gamepad virtual
(dpad/hat) usando uinput + evdev. El script lee 4 direcciones (UP/DOWN/LEFT/RIGHT),
aplica debounce por tiempo y emite eventos ABS_HAT0X/ABS_HAT0Y.

## Que hace
- Lee botones conectados a GPIO con pull-up interno (activo en LOW)
- Aplica debounce (10 ms por defecto)
- Crea un gamepad virtual llamado "DDR GPIO Dance Pad"
- Publica eje HAT X/Y (dpad) con baja latencia (2 ms)

## Pinout (BCM)
- UP:    GPIO 17
- LEFT:  GPIO 27
- DOWN:  GPIO 22
- RIGHT: GPIO 23

Los botones deben ir a GND (entrada activa en LOW).

## Requisitos
- Raspberry Pi con Linux
- Python 3
- Paquetes:
  - gpiozero
  - evdev
- Modulo uinput habilitado

Instalacion (Debian/Raspberry Pi OS):
```
sudo apt update
sudo apt install -y python3-gpiozero python3-evdev
sudo modprobe uinput
```

## Uso
```
python3 ddr_gpio_gamepad.py
```

El dispositivo virtual aparecera como "DDR GPIO Dance Pad".
Si necesitas permisos, ejecuta con sudo o agrega permisos a /dev/uinput.

## Ajustes rapidos
En `ddr_gpio_gamepad.py`:
- `polling_interval_seconds`: latencia (2 ms por defecto)
- `debounce_seconds`: debounce (10 ms por defecto)
- `gpio_bcm_pin_by_direction`: reasignar pines

## Notas
- Si falta `gpiozero`, el script muestra un mensaje con el comando de instalacion.
- El dpad no permite diagonales simultaneas en un mismo eje; cada eje se resuelve a -1, 0 o +1.
