"""Logger configuration that is used by all classes/functions in this project."""

import logging
import os

# CRITICAL = 50, FATAL = CRITICAL, ERROR = 40, WARNING = 30, INFO = 20, DEBUG = 10
LOGLEVEL = os.environ.get(
    "MUMASP_LOGLEVEL",
    20,
)

FMT = logging.Formatter(
    "{asctime} | {levelname} | {pathname} ({lineno}): {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)


def add_logfile_handler(
    logger: logging.Logger,
    fname: str,
) -> logging.FileHandler:
    """
    Add a file handler to a logger, i.e. make the logger log to the given file.

    Parameters
    ----------
    logger : logging.Logger
        The logger which should write to a log file.
    fname : str
        Path to the log file we want to write to.

    Returns
    -------
    handler : logging.FileHandler
        The file handler instance that was created.
    """
    file_handler = logging.FileHandler(
        fname,
        mode="a",
        encoding="utf-8",
    )
    logger.addHandler(file_handler)
    file_handler.setFormatter(FMT)

    return file_handler


def remove_logfile_handler(
    logger: logging.Logger,
    file_handler: logging.FileHandler,
) -> None:
    """
    Remove a file handler from a logger, i.e. stop a logger from writing to a log file.

    Parameters
    ----------
    logger : logging.Logger
        The logger which we want to stop from writing to a log file.
    file_handler : logging.FileHandler
        The file handler that is responsible for writing to the log file (was created using `add_logfile_handler()`).
    """
    logger.removeHandler(file_handler)


logger = logging.getLogger("MuMaSP")
logger.setLevel(LOGLEVEL)

console_handler = logging.StreamHandler()
logger.addHandler(console_handler)
console_handler.setFormatter(FMT)
