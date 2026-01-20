""""""

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
    max_trig: int = 10000,
    read_interval_s: float = 10,
    read_threshold: int = 100,
) -> tuple[int, float, list[int]]:
    """
    Run a measurement for the given telescope. The measurement is conducted for at most ``max_t_s`` seconds, or until ``max_trig`` triggers are recorded -- whichever happens first.

    Parameters
    ----------
    telescope : Telescope
        ...
    max_t_s: float
        ...
    max_trig: int
        ...
    read_interval_s: float
        ...
    read_threshold: int
        ...

    Returns
    -------
    int
    ...
    float
    ...
    list[int]
    ...
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
    """"""
    out_dir = Path(save_dir)
    if out_dir.is_dir():
        raise FileExistsError(
            f"Output directory '{save_dir}' already exists. Please choose a different output directory or delete '{save_dir}' to continue."
        )

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
    """"""
    scan(
        telescope=telescope,
        positions=[(theta, phi) for theta in thetas for phi in phis],
        **kwargs,
    )
