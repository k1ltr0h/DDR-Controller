# StepMania en Raspberry Pi 3B (ARM 32-bit) + DDR Controller (GPIO → Gamepad)

Este repositorio/documentación deja funcionando **StepMania compilado desde fuente** en una **Raspberry Pi 3 Model B (armhf / 32-bit)** y un **pad DDR por GPIO** expuesto al sistema como un **gamepad virtual** usando **uinput + evdev**.

Se verificó que la build compilada **no crashea en el menú** (a diferencia de algunas versiones precompiladas usadas previamente).

---

## 1) Compilar StepMania desde el repo

### Dependencias (build + runtime)

Instala toolchain y librerías típicas (X11/OpenGL/audio y dependencias comunes usadas por StepMania):

```bash
sudo apt update
sudo apt install -y \
  git cmake build-essential pkg-config \
  libgl1-mesa-dev libglu1-mesa-dev \
  libx11-dev libxext-dev libxrandr-dev libxt-dev libsm-dev libice-dev \
  libasound2-dev libpulse-dev \
  libmad0-dev libbz2-dev zlib1g-dev \
  libjpeg-dev libpcre3-dev libogg-dev libvorbis-dev

```

### Clonar y compilar

```bash
cd ~
gitclone https://github.com/stepmania/stepmania.git
cd stepmania
mkdir -p build
cd build
cmake ..
make -j1

```

> Nota: en Raspberry Pi (ARM) se evitó construir componentes pensados para x86 (por ejemplo Minimaid/libmmmagic). Si tu CMake expone opción, puedes desactivarlo explícitamente con:
>  
>  
>  

```bash
> cmake -DWITH_MINIMAID=OFF ..
> 
> ```

>  

---

## 2) Ejecutar StepMania correctamente (paths, Save y Logs)

Ejecuta desde el directorio del juego (donde existen `Themes/` , `Songs/` , etc.):

```bash
cd ~/stepmania
mkdir -p Save
./stepmania

```

### Logs reales

Los logs se escriben en el home del usuario, por ejemplo:

* `~/.stepmania-5.0/Logs/log.txt`
* `~/.stepmania-5.0/Logs/info.txt`
* `~/.stepmania-5.0/Logs/userlog.txt`

---

## 3) Forzar detección del input (LinuxEvent)

Para que StepMania detecte correctamente dispositivos por `/dev/input/event*` , se forzó el driver de input en:

 `~/stepmania/Save/Preferences.ini`

```
InputDrivers=LinuxEvent,X11

```

Comando usado:

```bash
sed -i's/^InputDrivers=.*/InputDrivers=LinuxEvent,X11/' ~/stepmania/Save/Preferences.ini

```

Verificación rápida en log:

```bash
grep -iE"Input device:|LinuxEvent|Joystick|Not a joystick|/dev/input" ~/.stepmania-5.0/Logs/log.txt |tail -n 200

```

> Nota: si ves “Resource temporarily unavailable”, normalmente es porque otro proceso está leyendo el dispositivo en modo exclusivo. Cierra evtest u otra app que esté tomando el event mientras pruebas StepMania.
>  

---

# DDR Controller (GPIO -> Gamepad)

Convierte un pad DDR conectado a los GPIO de una Raspberry Pi en un gamepad virtual

(dpad/hat) usando uinput + evdev. El script lee 4 direcciones (UP/DOWN/LEFT/RIGHT), 

aplica debounce por tiempo y emite eventos ABS_HAT0X/ABS_HAT0Y.

## Que hace

* Lee botones conectados a GPIO con pull-up interno (activo en LOW)
* Aplica debounce (10 ms por defecto)
* Crea un gamepad virtual llamado "DDR GPIO Dance Pad"
* Publica eje HAT X/Y (dpad) con baja latencia (2 ms)

## Pinout (BCM)

* UP: GPIO 17
* LEFT: GPIO 27
* DOWN: GPIO 22
* RIGHT: GPIO 23

Los botones deben ir a GND (entrada activa en LOW).

## Requisitos

* Raspberry Pi con Linux
* Python 3
* Paquetes:
    - gpiozero
    - evdev
* Modulo uinput habilitado

Instalacion (Debian/Raspberry Pi OS):

```bash
sudo apt update
sudo apt install -y python3-gpiozero python3-evdev
sudo modprobe uinput

```

## Uso

```bash
python3 ddr_gpio_gamepad.py

```

El dispositivo virtual aparecera como "DDR GPIO Dance Pad".

Si necesitas permisos, ejecuta con sudo o agrega permisos a /dev/uinput.

## Ajustes rapidos

En `ddr_gpio_gamepad.py` :

* `polling_interval_seconds`: latencia (2 ms por defecto)
* `debounce_seconds`: debounce (10 ms por defecto)
* `gpio_bcm_pin_by_direction`: reasignar pines

## Notas

* Si falta `gpiozero`, el script muestra un mensaje con el comando de instalacion.
* El dpad no permite diagonales simultaneas en un mismo eje; cada eje se resuelve a -1, 0 o +1.

---

## 4) Hacer que StepMania vea el “DDR GPIO Dance Pad”

1. Levanta el controlador (crea el dispositivo virtual):

```bash
python3 ddr_gpio_gamepad.py

```

1. Verifica que el sistema lo ve (ejemplo con evtest):

```bash
evtest
# Selecciona el device: "DDR GPIO Dance Pad"

```

1. Ejecuta StepMania (con `InputDrivers=LinuxEvent,X11` ya configurado).

---

## 5) Audio: salida por jack 3.5mm (no HDMI)

Para que el audio salga por el jack:

```bash
sudo raspi-config

```

Luego: **System Options → Audio → Headphones**.

Ver tarjetas ALSA:

```bash
cat /proc/asound/cards
aplay -l

```

Subir volumen (jack suele ser `card 1` ):

```bash
amixer -c 1 sset'Master' 90% unmute ||true
amixer -c 1 sset'Headphone' 90% unmute ||true
amixer -c 1 sset'PCM' 90% unmute ||true

```

Prueba directa al jack:

```bash
aplay -D plughw:1,0 /usr/share/sounds/alsa/Front_Center.wav
```
