"""Convenience functions for performing measurements with the muon telescope."""

import json
import os
import time
from pathlib import Path

from . import __version__
from .logger import add_logfile_handler, logger, remove_logfile_handler
from .telescope import Telescope


def measure(
    telescope: Telescope,
    max_t_s: float = 3600,
    max_trig: int = 1000,
    read_interval_s: float = 10.0,
    read_threshold: int = 100,
) -> tuple[int, float, list[int]]:
    """
    Run a measurement for the given telescope. The measurement is conducted for at most ``max_t_s`` seconds, or until ``max_trig`` triggers are recorded -- whichever happens first.

    Parameters
    ----------
    telescope : Telescope
        The instance of the muon telescope to perform the measurement on.
    max_t_s: float, optional
        Maximum number of seconds to measure. If `max_trig` is reached first, the measurement is stopped before this number of seconds is reached. Defaults to 3600 (one hour).
    max_trig: int, optional
        Maximum number of triggers to record before finishing the measurement. If `max_t_s` is reached first, the measurement is stopped before this number of triggers is reached. Defaults to 1000 triggers.
    read_interval_s: float, optional
        Number of seconds between two queries of the Arduino (every `read_interval_s` the number of triggers in the Arduino's memory is read). Has to be short enough to not risk overflowing the Arduino's memory (1000 triggers). Defaults to 10 seconds.
    read_threshold: int, optional
        Number of triggers to wait for before reading and emptying the Arduino's memory.

    Returns
    -------
    t_start: int
        The start UNIX timestamp (according to your computer's clock) of the measurement.
    time_elapsed: float
        The time (in seconds) between starting and stopping the measurement.
    triggers: list[int]
        A list of all trigger UNIX timestamps (according to the Arduino's clock).

    Examples
    --------
    >>> import mumasp
    >>> t = mumasp.Telescope()
    >>> t.calibrate()

    Now move the telescope to the vertical position
    >>> t.move_to(theta=0, phi=0)

    Start a measurement for one minute
    >>> from mumasp.measurement import measure
    >>> _, time_elapsed, triggers = measure(telescope, max_t_s=60)

    Compute the rate (in Hz)
    >>> rate = len(triggers) / time_elapsed
    """
    telescope.clear_buffer()

    t_start = time.time()
    n_triggers = 0
    triggers = []

    while time.time() - t_start < max_t_s:
        time.sleep(read_interval_s)

        n_in_buffer = telescope.read_ntrig()

        if n_in_buffer >= read_threshold:
            # Read timestamps from arduino buffer (clears the buffer)
            new_triggers = telescope.read_buffer()
            n_in_buffer = 0
            n_triggers += len(new_triggers)
            triggers.extend(new_triggers)

        if n_triggers + n_in_buffer >= max_trig:
            break

    t_end = time.time()
    triggers.extend(telescope.read_buffer())

    time_elapsed = t_end - t_start

    return t_start, time_elapsed, triggers


def scan(
    telescope: Telescope,
    positions: list[tuple[float, float]],
    save_dir: str,
    skip_existing: bool = True,
    **kwargs: dict,
) -> None:
    """
    Perform a measurement for all (theta, phi) positions in `positions` and write the measurement results to `save_dir`. Details regarding a single measurement are controlled by keyword arguments.

    Parameters
    ----------
    telescope : Telescope
        The instance of the muon telescope to perform the measurement on.
    positions: list[tuple[float, float]]
        List of (theta, phi) pairs of positions to perform the measurements in.
    save_dir: str
        The output directory for measurement files.
    skip_existing: bool, optional
        If True, positions that were already successfully measured are skipped. Defaults to True.
    **kwargs
        Extra arguments for `measure`: refer to its documentation for a list of all possible arguments.

    Examples
    --------
    >>> import mumasp
    >>> from mumasp.measurement import scan
    >>> t = mumasp.Telescope()
    >>> t.calibrate()

    Now perform measurement in three positions, where each position is measured for 10 minutes (600 seconds).
    >>> scan(t, [(0, 0), (45, 0), (90, 0)], "test_output/", max_t_s=600)

    See Also
    --------
    measure : Perform a single measurement.
    """
    out_dir = Path(save_dir)

    if not all(isinstance(x, tuple) and len(x) == 2 and all(isinstance(y, (float, int)) for y in x) for x in positions):
        raise ValueError("Input argument 'positions' must be a list of 2-tuples of floats or integers.")

    os.mkdir(out_dir)
    logfile_handler = add_logfile_handler(logger, out_dir / Path("mumasp.log"))

    n = len(positions)

    try:
        for k, (theta, phi) in enumerate(positions):
            out_path = out_dir / Path(f"meas_t{theta:.2f}_p{phi:.2f}.txt")
            if skip_existing and out_path.exists():
                logger.info(
                    f"Skipped measurement {k}/{n} because file for theta={theta:.2f}° and phi={phi:.2f}° already exists."
                )
                continue

            logger.info(f"Measurement {k}/{n} for theta={theta:.2f}° and phi={phi:.2f}° ...")

            telescope.move_to(theta=theta, phi=phi)

            t_start, time_elapsed, triggers = measure(
                telescope=telescope,
                **kwargs,
            )

            info_dict = {
                "theta_deg": theta,
                "phi_deg": phi,
                "n_triggers": len(triggers),
                "t_start_s": t_start,
                "t_elapsed_s": time_elapsed,
                "version": __version__,
            }
            info_str = json.dumps(info_dict)

            with open(out_path, "w") as f:
                f.writelines([info_str] + triggers)

            logger.info(f"Measurement finished. Written to {out_path}. Info: {info_str}")
    finally:
        remove_logfile_handler(logger, logfile_handler)


def raster_scan(
    telescope: Telescope,
    thetas: list[float],
    phis: list[float],
    **kwargs: dict,
) -> None:
    """
    Perform a measurement for all (theta, phi) combinations in `thetas` and `phis`. The behavior is otherwise identical to `scan`.

    Parameters
    ----------
    telescope : Telescope
        The instance of the muon telescope to perform the measurement on.
    thetas: list[float]
        List of theta values.
    phis: list[float]
        List of phi values.
    **kwargs
        Extra arguments for `measure` or `scan`: refer to their documentations for a list of all possible arguments.

    See Also
    --------
    measure : Perform a single measurement.
    scan: Perform measurements for several telescope positions.
    """
    scan(
        telescope=telescope,
        positions=[(theta, phi) for theta in thetas for phi in phis],
        **kwargs,
    )
