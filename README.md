<h1 align="center">
<img src="logo/mumasp.png" alt="logo" width="200"/>
</h1>

# Project description
Small project to operate a muon telescope.

A stack of 4 plastic scintillator panels (20 cm x 20 cm, 2 m apart), each connected to an H10721P-110 photo multiplier (PMT), is mounted on a frame that can be tilted and rotated freely by stepping motors. 

When a cosmogenic muon crosses the scintillator panels, it generates a signal on the respective PMT's output. Depending on its incident angle, it might or might not hit several of the panels. If it hits *all* panels, the incident angle is aligned with the telescope's current axis, with an uncertainty calculated from the size of the panels and their relative distance.
Furthermore, requiring multiple PMTs to trigger reduces the chance of getting false alarms -- *dark counts*.

The PMTs' signals are shaped and a dedicated electronics board detects time coincident triggers (if all 4 PMTs trigger, the board outputs a trigger). These triggers are read out using an Arduino. The Arduino also controls the stepping motors. 

The Arduino operates autonomously and can be controlled via its ethernet port. However, it can only store 1000 triggers at a time. Therefore, it has to be read out periodically (again using the ethernet connection). To avoid having a laptop connected at all times, a Raspberry Pi is used to take on this task.

This package implements an API for the Arduino, with convenience functions for moving the telescope to a specified angle, read triggers from the arduino, as well as extended functionality like performing a grid scan of several angle combinations and saving the results to files. It can be run either on a separate computer or on the aforementioned Raspberry Pi.

# Installation
Clone this repository and install it 
```
$ git clone https://github.com/philipp-schreiner/mumasp.git
$ cd mumasp
$ python3 -m pip install .
```
or install it in editable mode (such that it automatically updates the package when you pull a new version of the repository):
```
$ python3 -m pip install -e .
```

## Connecting to the Arduino
The Arduino has the static IP address `192.168.99.99`. To connect, you have to establish a direct ethernet connection between the Arduino and your computer and configure the network adapter on your computer to have a `192.168.99.X` IP address (e.g. `192.168.99.98`) and a subnet mask of `255.255.255.0`.

On MacOS and Windows, this can easily be done in the network settings. On Linux, you can use (change `eth0` to the correct interface)
```
ifconfig eth0 192.168.99.98 netmask 255.255.255.0
```

## Connecting to the Raspberry Pi
This repository was cloned to `/opt/software/mumasp` and installed into a dedicated virtual environment (`/opt/software/envs/venv_mumasp`), which is automatically activated when you log into the Raspberry Pi. The installation is editable, meaning that it updates when you pull a new version of the repository. 

To connect to the Raspberry Pi, make sure your PC is connected to the same network as the telescope. Then log in via SSH:
```
ssh muon@mumasp-pi.local
```

# Getting started
Once you established a connection to the Arduino, start a Python session, import this package, instantiate the telescope, and check if everything works by printing the Arduino's help message:
```
import mumasp

t = mumasp.Telescope()
t.help()
```
If the call to `.help()` times out, check your connection again.

The very first step is to calibrate the telescope's axes: Align (on the physical telescope) the red dots on both axes (this puts the axes in a more or less defined position). Then run
```
t.calibrate()
```
which will slowly move the axis until they are perfectly aligned. If successful, you can now tell the telescope to move to any angle (theta, phi) with `theta = 0 ... 180` and `phi = 0 ... 360` (in degrees)
```
t.move_to(theta=0, phi=90)
```

# Measuring
... TODO


# Acknowledgements
We thank the Hochschuljubiläumsfonds of the city of Vienna for supporting this project.