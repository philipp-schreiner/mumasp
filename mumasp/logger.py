""""""

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
    """TODO:"""
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
    """TODO:"""
    logger.removeHandler(file_handler)


logger = logging.getLogger("MuMaSP")
logger.setLevel(LOGLEVEL)

console_handler = logging.StreamHandler()
logger.addHandler(console_handler)
console_handler.setFormatter(FMT)
