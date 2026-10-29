# pedals2rudder

Use two **racing pedals** (gas + brake) as **flight-sim rudder pedals** with **wheel brakes**.

- left pedal → rudder left
- right pedal → rudder right
- **both pedals together → wheel brakes** (left and right toe brake), rudder stays straight

Works with any pedal set Windows sees as a game controller (MOZA, Logitech, Thrustmaster, Fanatec…) and any simulator that accepts a joystick axis: X-Plane 11/12, MSFS 2020/2024, DCS, IL-2, Condor.

Tested with MOZA R3 + SR-P Lite pedals in X-Plane 11 on Windows 10.

Русская версия ниже ↓

---

## How it works

Racing pedals are two separate one-way axes. A rudder is one axis with a centre. This program reads both pedals, combines them into one centred axis and sends it to a **vJoy** virtual joystick. The sim then sees a normal rudder axis plus two toe-brake axes.

Unlike a plain "merge axis" in Joystick Gremlin or UCR, pressing both pedals here does not just cancel out: it **brakes**. The brake force is how far the *less* pressed pedal is down. A difference between the pedals of up to 30 % counts as "together" and does not move the rudder, so you can brake in a straight line without fighting the yaw.

## Install (once)

1. **Python 3.9 or newer** — https://www.python.org/downloads/windows/
   During install tick **"Add python.exe to PATH"**.
2. Open a command prompt and run:
   ```
   pip install pygame-ce
   ```
3. **vJoy driver** — https://github.com/BrunnerInnovation/vJoy/releases (download the `vJoySetup.exe`, install, reboot if asked).
4. Start **Configure vJoy** from the Start menu. Device 1: tick axes **X, Y, Z**, click **Apply**.
5. Download this repository (green **Code** button → **Download ZIP**) and unpack it anywhere, e.g. `C:\pedals2rudder`.

## Run

Double-click **`Start rudder.bat`** (or run `python rudder.py`).

First start = setup. The program asks you to:
1. release both pedals and press Enter;
2. press and hold the **left** pedal, press Enter, release, Enter;
3. press and hold the **right** pedal, press Enter, release, Enter.

It then measures the vJoy axis mapping automatically and saves everything to `rudder_config.json`. From now on just double-click `Start rudder.bat` before you fly and **keep the window open**. Ctrl+C or closing the window stops it and centres the rudder.

The window shows live values:
```
  pedals L   0% R  60%   rudder [----------|-----O----] +0.60   brake [..........]   0%
```

Other commands:

| Command | What it does |
|---|---|
| `Setup pedals.bat` / `python rudder.py --setup` | choose the pedals and axes again |
| `python rudder.py --calibrate` | re-measure the vJoy axis mapping only |
| `python rudder.py --check` | list controllers, test vJoy, exit |

## Set up your simulator (once)

Start `Start rudder.bat` **first**, then the sim. In the sim's joystick settings look for a device called **vJoy Device**:

| vJoy axis | Assign to |
|---|---|
| X | rudder / yaw |
| Y | left toe brake |
| Z | right toe brake |

Then **calibrate** the vJoy device in the sim (X-Plane: Settings → Joystick → Calibrate; press each pedal to the floor, then both). If the pedals are also listed as their own device in the sim, make sure they are **not** assigned to anything there, otherwise the two will fight. Tip: in X-Plane, do the calibration with the program running and press left, right, then both pedals fully.

### X-Plane 11 / 12
Settings → Joystick → select **vJoy Device** → Axis 0 (X) = **Yaw**, Axis 1 (Y) = **Left toe brake**, Axis 2 (Z) = **Right toe brake** → **Calibrate**.

### MSFS 2020 / 2024
Options → Controls → vJoy Device → **Rudder axis** = joystick X axis, **Brakes left/right axis** = Y / Z. Set sensitivity to linear, no dead zone (the program already has one).

### DCS / IL-2 / Condor
Assign the vJoy X axis to rudder and Y / Z to the wheel brakes in the same way.

## Tuning (`rudder_config.json`)

| Key | Default | Meaning |
|---|---|---|
| `invert` | `false` | set `true` if left/right are swapped |
| `deadzone` | `0.04` | pedal travel ignored at rest (4 %) |
| `brake_min` | `0.15` | both pedals must be at least this far down (15 %) to brake |
| `brake_tol` | `0.30` | pedal difference treated as "together" (30 %) |
| `vjoy` | measured | raw vJoy values for −1 / 0 / +1; re-measure with `--calibrate` |

Edit the file in Notepad and restart the program.

## Troubleshooting

- **"No game controller found"** — the pedal base is off, not plugged in, or its own software (e.g. MOZA Pit House) holds the device. Power it on, close that software, retry.
- **"No pedal movement seen"** during setup — hold the pedal to the floor *while* pressing Enter. If it still fails, check the pedal cable into the base.
- **"vJoy Device 1 is in use"** — close Joystick Gremlin, UCR or another copy of this program.
- **"vJoy Device 1 does not exist"** — open Configure vJoy, enable Device 1 with X, Y, Z, Apply.
- **Sim does not see "vJoy Device"** — some sims only list devices present at start: start this program before the sim. If the physical pedals confuse the sim, hide them with [HidHide](https://github.com/nefarius/HidHide).
- **Rudder slightly off-centre in the sim** — run `python rudder.py --calibrate`, then re-calibrate the vJoy device inside the sim.
- **Pedals read −1 but nothing happens after a Windows update / re-plug** — Windows may have renumbered the axes. Run `Setup pedals.bat` again.

## Tests

```
python tests/test_mix.py
```
Checks the mixing maths (no hardware needed).

## License

MIT — see `LICENSE`. vJoy is a separate project with its own license and is not bundled here.

---

# pedals2rudder (по-русски)

Две **гоночные педали** (газ + тормоз) работают как **педали руля направления** в авиасимуляторе, а нажатые **вместе** — как **тормоза колёс**.

- левая педаль → руль влево
- правая педаль → руль вправо
- **обе вместе → торможение** (левая и правая стойка), руль остаётся прямо

Подходит для любых педалей, которые Windows видит как игровое устройство (MOZA, Logitech, Thrustmaster, Fanatec), и любого симулятора: X-Plane 11/12, MSFS 2020/2024, DCS, IL-2, Condor. Проверено на MOZA R3 + SR-P Lite в X-Plane 11, Windows 10.

## Как это работает

Гоночные педали — две отдельные односторонние оси, а руль — одна ось с центром. Программа читает обе педали, сводит их в одну ось с центром и отдаёт виртуальному джойстику **vJoy**. Симулятор видит обычный руль и две оси тормозов.

В отличие от простого «слияния осей» в Joystick Gremlin или UCR, здесь нажатие обеих педалей не обнуляет руль, а **тормозит**. Сила тормоза — насколько выжата *менее* нажатая педаль. Разница между педалями до 30 % считается «одновременно» и на руль не влияет, поэтому можно тормозить по прямой.

## Установка (один раз)

1. **Python 3.9 или новее** — https://www.python.org/downloads/windows/ — при установке поставь галочку **"Add python.exe to PATH"**.
2. В командной строке: `pip install pygame-ce`
3. **Драйвер vJoy** — https://github.com/BrunnerInnovation/vJoy/releases (файл `vJoySetup.exe`).
4. Запусти **Configure vJoy** из меню Пуск: Device 1 → галочки на осях **X, Y, Z** → **Apply**.
5. Скачай этот репозиторий (зелёная кнопка **Code** → **Download ZIP**) и распакуй в любую папку.

## Запуск

Двойной клик по **`Start rudder.bat`**. Первый запуск — настройка: отпусти обе педали, Enter; нажми и держи **левую**, Enter, отпусти, Enter; то же с **правой**. Программа сама измерит калибровку vJoy и сохранит всё в `rudder_config.json`. Дальше — просто запускай перед полётом и **не закрывай окно**. Ctrl+C или закрытие окна — остановка, руль в нейтрали.

`Setup pedals.bat` — настроить педали заново. `python rudder.py --calibrate` — перемерить только vJoy. `python rudder.py --check` — показать устройства и выйти.

## Настройка симулятора (один раз)

Сначала запусти программу, потом сим. В настройках джойстика найди **vJoy Device**: ось **X → руль (Yaw)**, **Y → левый тормоз (Left toe brake)**, **Z → правый тормоз (Right toe brake)**. Затем **калибровка** (X-Plane: Settings → Joystick → Calibrate; нажми до упора левую, правую, потом обе). Сами педали в симуляторе ни на что назначены быть **не должны**, иначе два устройства будут мешать друг другу.

## Если что-то не так

- **«No game controller found»** — база педалей выключена, не подключена, или её занимает фирменная программа (MOZA Pit House). Включи, закрой программу, повтори.
- **«No pedal movement seen»** — держи педаль в полу *в момент* нажатия Enter. Если не помогает — проверь кабель педалей в базу.
- **«vJoy Device 1 is in use»** — закрой Joystick Gremlin, UCR или вторую копию программы.
- **Сим не видит vJoy Device** — запускай программу до сима. Если мешают физические педали — спрячь их через [HidHide](https://github.com/nefarius/HidHide).
- **Руль чуть смещён от центра** — `python rudder.py --calibrate`, потом калибровка vJoy в симе.
- **Перепутаны стороны** — в `rudder_config.json` поставь `"invert": true`.
- **После обновления Windows педали перестали работать** — Windows перенумеровала оси. Запусти `Setup pedals.bat` ещё раз.

Лицензия MIT. vJoy — отдельный проект со своей лицензией, сюда не входит.
