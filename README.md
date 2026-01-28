<h1 align="center">
<img src="doc/logo/mumasp.png" alt="logo" width="200"/>
</h1>

Small project to operate a muon telescope.

# Project description

A stack of four BC-408 plastic scintillator panels (20 cm x 20 cm, 2 m apart), each connected to an H10721P-110 photo multiplier (PMT), is mounted on a frame that can be tilted and rotated freely by stepping motors. 

When a cosmogenic muon crosses the scintillator panels, it generates a signal on the respective PMT's output. Depending on its incident angle, it might or might not hit several of the panels. If it hits *all* panels, the incident angle is aligned with the telescope's current axis, with an uncertainty calculated from the size of the panels and their relative distance.
Furthermore, requiring multiple PMTs to trigger reduces the chance of getting false alarms -- *dark counts*.

The PMTs' signals are shaped and a dedicated electronics board detects time coincident triggers (if all 4 PMTs trigger, the board outputs a trigger). These triggers are read out using an Arduino. The Arduino also controls the stepping motors. 

The Arduino operates autonomously and can be controlled via its ethernet port. However, it can only store 1000 triggers at a time. Therefore, it has to be read out periodically (again using the ethernet connection). To avoid having a laptop connected at all times, a Raspberry Pi is used to take on this task.

This package implements an API for the Arduino, with convenience functions for moving the telescope to a specified angle, read triggers from the arduino, as well as extended functionality like performing a grid scan of several angle combinations and saving the results to files. It can be run either on a separate computer or on the aforementioned Raspberry Pi.

# Installation
Clone this repository and install it 
```shell
$ git clone https://github.com/philipp-schreiner/mumasp.git
$ cd mumasp
$ python3 -m pip install .
```
or install it in editable mode (such that it automatically updates the package when you pull a new version of the repository):
```shell
$ python3 -m pip install -e .
```

## Connecting to the Arduino
The Arduino has the static IP address `192.168.99.99`. To connect, you have to establish a direct ethernet connection between the Arduino and your computer and configure the network adapter on your computer to have a `192.168.99.X` IP address (e.g. `192.168.99.98`) and a subnet mask of `255.255.255.0`.

On MacOS and Windows, this can easily be done in the network settings. On Linux, you can use (change `eth0` to the correct interface)
```shell
$ ifconfig eth0 192.168.99.98 netmask 255.255.255.0
```

## Connecting to the Raspberry Pi
This repository was cloned to `/opt/software/mumasp` and installed into a dedicated virtual environment (`/opt/software/envs/venv_mumasp`), which is automatically activated when you log into the Raspberry Pi. The installation is editable, meaning that it updates when you pull a new version of the repository. 

To connect to the Raspberry Pi, make sure your PC is connected to the same network as the telescope. Then log in via SSH:
```shell
$ ssh muon@mumasp-pi.local
```

# Getting started
Once you established a connection to the Arduino, start a Python session, import this package, instantiate the telescope, and check if everything works by printing the Arduino's help message:
```python
import mumasp

t = mumasp.Telescope()
t.help()
```
If the call to `.help()` times out, check your connection again.

The very first step is to calibrate the telescope's axes: Align (on the physical telescope) the red dots on both axes (this puts the axes in a more or less defined position). Then run
```python
t.calibrate()
```
which will slowly move the axis until they are perfectly aligned. If successful, you can now tell the telescope to move to any angle (theta, phi) with `theta = 0 ... 180` and `phi = 0 ... 360` (in degrees)
```python
t.move_to(theta=0, phi=90)
```

# Measuring
To perform measurements, the package provides convenience functions in the `mumasp.measurement` submodule.

```python
from mumasp.measurement import measure, scan, raster_scan
```

- `measure` measures for a given amount of time or until a given number of triggers has been recorded:
    ```python
    # 't_start' is the start timestamp of the measurement.
    # 'time_elapsed' is the duration (in seconds) of the measurement.
    # 'triggers' is a list of integer timestamps of muon triggers.
    t_start, time_elapsed, triggers = measure(t, max_t_s=60)
    ```

- `scan` moves the telescope to all positions in a list, measures in all of them for a given amount of time (or until a given number of triggers has been recorded), and saves the results to files.
    ```python
    # Measure in positions (0, 0), (45, 0), and (90, 0) for at most 10 minutes (each) and save the results into directory 'test_output/'.
    scan(
        t, 
        [(0, 0), (45, 0), (90, 0)],
        "test_output/", 
        max_t_s=600,
    )
    ```
- `raster_scan` does the same as `scan` but builds the positions from combinations of `theta` and `phi` values in a list.
    ```python
    # Measure for theta values between 0° and 90°, and phi values between 0° and 360° in 20° increments and save the results to 'test_output/'.
    raster_scan(
        t,
        thetas=list(range(10, 90, 20)),
        phis=list(range(10, 360, 20)),
        save_dir="test_output/",
        max_t_s=600,
    )
    ```

# Evaluating results
> [!NOTE]
> We use `numpy` and `matplotlib` for processing the results. Those aren't dependencies of `mumasp`, so you have to install them additionally.

Once a `scan` (or `raster_scan`) has been completed, the results can be loaded from the files in the previously created folder:
```python
import numpy as np
import matplotlib.pyplot as plt

from mumasp.measurement import load

# The dictionary contains all start timestamps, theta and phi values, durations, as well as trigger timestamps as lists.
data_dict = load("test_output/")   
```
You can access the angle values as well as the counts recorded in those positions and the measuring times like so:
```python
theta, phi = np.array(data_dict["theta_deg"]), np.array(d["phi_deg"])
n_trigs = np.array(data_dict["n_triggers"])
t_meas = np.array(d["t_elapsed_s"])
```
Typically, the muon flux is reported in units of cm⁻²s⁻¹sr⁻¹. The active solid angle (in sr) of the telescope is given by the pyramid which is defined by connecting the corners of the outermost panels that are active. Let $d$ be the distance between those panels and $a=20\,$cm the side length of the scintillator panels. Then [[1]](https://en.wikipedia.org/wiki/Solid_angle#Pyramid)

$$\Omega=4\,\arctan\frac{a^2}{d\sqrt{d^2+2a^2}}.$$

For $d=197\,$cm, this gives $\Omega=0.04\,$sr. For $d=64.5\,$cm, we get $\Omega=0.35\,$sr. Double check which panels were active and what their distance was in your measurement. The flux is then normalized as follows:
```python
def solid_angle(d_cm: float, a_cm: float = 20.):
    return 4*np.arctan(a_cm**2 /(d_cm * np.sqrt(d_cm**2+2*a_cm**2)))

panel_distance = 197 # cm
panel_side_length = 20 # cm
omega = omega = solid_angle(panel_distance) # sr
panel_area = panel_side_length**2 # cm^2

rate_trigs = n_trigs/t_meas/omega/panel_area # 1/(cm^2 s sr)
```
It might also be useful to arrange the results in a $(\theta,\phi)$-grid:
```python
theta_grid, phi_grid = np.meshgrid(
    np.sort(np.unique(theta)), 
    np.sort(np.unique(phi))
)
rates = np.zeros(pos_theta.shape, dtype=np.float32)

for t, p, r in zip(theta, phi, rate_trigs):
    i = theta_grid == t
    j = phi_grid == p
    rates[i*j] = r
```
Now, `theta_grid` and `phi_grid` are meshgrids and `rates` is the corresponding 2D array of flux values. We can plot them in a polar plot:
```python
fig, ax = plt.subplots(1, 1, subplot_kw=dict(projection="polar"))
pcm = ax.pcolormesh(
    phi_grid/180*np.pi, 
    theta_grid, 
    rates, 
    shading="nearest",
    cmap="Blues",
)
fig.colorbar(pcm, orientation='vertical', pad=0.1, label="flux (cm$^{-2}\,$sr$^{-1}\,$s$^{-1}$)")
```
![](doc/img/example_output.png)

# Acknowledgements
We thank the Hochschuljubiläumsfonds of the city of Vienna for supporting this project.