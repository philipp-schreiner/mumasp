""""""

import socket
import time

from .logger import logger


class Telescope:
    """"""
    # These config entries have to match those in the Arduino code!
    _arduino_conf = {
        "IP": "192.168.99.99",
        "port": 1033,
    }

    _stepping_motor_conf = {
        "steps_per_rev_phi": 12800,
        "steps_per_rev_theta": 12800,
    }

    def __init__(
        self,
        timeout: float = 60.0,
    ) -> None:
        self._timeout = timeout

        self._calibrated = False
        self._current_pos = (None, None)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(IP={self._arduino_conf['IP']}, calibrated={self.is_calibrated}, position={self.position})"

    def send_cmd(self, cmd: str) -> str:
        """Send a command to the arduino."""
        response = ""

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self._timeout)
                s.connect((self._arduino_conf["IP"], self._arduino_conf["port"]))
                s.sendall((cmd + "\r\n").encode())

                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    response += data.decode("utf-8", errors="replace")

        except socket.timeout:
            logger.error("No response from Arduino. Are you sure it is connected?")

        return response.strip()

    def help(self) -> None:
        """Print help for Arduino communication."""
        print(self.send_cmd("?"))

    def clear_buffer(self) -> None:
        """Clear arduino trigger buffer."""
        logger.info(f"Buffer cleared. Response: {self.send_cmd('x')}")

    def read_ntrig(self) -> int:
        """Return the number of triggers in the arduino's buffer."""
        return int(self.send_cmd("n"))

    def read_buffer(self) -> list[int]:
        """Read arduino trigger buffer."""
        # Discard first line (number of triggers)
        reply_lines = self.send_cmd("h").splitlines()[1:]
        sanitized_lines = [ln.strip() for ln in reply_lines if ln.strip()]

        return [int(ln) for ln in sanitized_lines]

    def calibrate(self) -> None:
        """Calibrate the axes of the telescope."""
        if self._calibrated:
            logger.warning("MuMaSP has already been calibrated before.")
            return

        for ax in [0, 1]:
            response = self.send_cmd(f"c{ax}")

            # We only check responses 0 and -3 because no other return codes
            # are possible with how we call it here.
            if response == "0":
                logger.info(f"Calibration of axis {ax} successful. Response: {response}")
            elif response == "-3":
                msg = f"Calibration failed for axis {ax}: End switch not found after full turn. Response {response}"
                logger.error(msg)
                raise ValueError(msg)
            else:
                msg = f"Unexpected response while trying to calibrate axis {ax}: Response: {response}"
                logger.error(msg)
                ValueError(msg)

            time.sleep(1)

        self._calibrated = True
        self._current_pos = (90.0, 0.0)

    def move_to(self, theta: float, phi: float) -> None:
        """
        Move the telescope to angles theta (azimuthal, 0-90°) and phi (polar, 0-360°).

        Parameters
        ----------
        theta : float
            ...
        phi : float
            ...
        """
        if not self._calibrated:
            msg = "Telescope must be calibrated before moving it."
            logger.error(msg)
            raise Exception(msg)

        if not (theta >= 0 and phi >= 0):
            msg = "Both theta and phi have to be non-negative."
            logger.error(msg)
            raise ValueError(msg)

        if abs(phi % 360 - self._current_pos[1]) < 1e-10:
            logger.info(f"Already at phi={phi % 360}.")
        else:
            steps_phi = int(round(self._stepping_motor_conf["steps_per_rev_phi"] / 360.0 * (phi % 360)))
            logger.info(f"Moving to phi={phi % 360} ...")
            response = self.send_cmd(f"m0,{steps_phi}")
            if response != "0":
                logger.error(f"Moving to phi={phi % 360} failed. Response: {response}")

        if abs(theta % 180 - self._current_pos[0]) < 1e-10:
            logger.info(f"Already at theta={theta % 180}.")
        else:
            steps_theta = int(round(self._stepping_motor_conf["steps_per_rev_theta"] / 360.0 * (theta % 180)))
            logger.info(f"Moving to theta={theta % 180} ...")
            response = self.send_cmd(f"m1,{steps_theta}")
            if response != "0":
                logger.error(f"Moving to theta={theta % 180} failed. Response: {response}")

        self._current_pos = (theta % 180, phi % 360)

    def reset_position(self) -> None:
        """Return to the starting position (from which a new calibration can be attempted)."""
        self.move_to(theta=60, phi=40)
        self._calibrated = False

    @property
    def is_calibrated(self) -> bool:
        """True if telescope has been successfully calibrated."""
        return self._calibrated

    @property
    def position(self) -> tuple[float, float]:
        """Return the current (theta, phi) position that the telescope is facing."""
        return self._current_pos

    @property
    def arduino_date(self) -> str:
        """Return the current date according to the clock on the arduino."""
        return self.send_cmd("r")

    @arduino_date.setter
    def arduino_date(self, val: list[int]) -> None:
        """
        Set the arduino's date to 'Y,m,d,H,M,S'.

        Parameters
        ----------
        val : list[int]
            ...
        """
        if (len(val) != 6) or not all(isinstance(x, int) for x in val):
            raise ValueError("Input date has to be a list of 6 integers.")

        response = self.send_cmd("s" + ",".join(val))

        if response == "0":
            print(f"Successfully changed arduino date. Response: {response}")
        else:
            print(f"Changing arduino date failed. Response: {response}")
