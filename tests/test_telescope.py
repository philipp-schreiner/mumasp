"""Test the Telescope API."""

import pytest

from .fixtures import test_telescope


def test_repr(test_telescope):
    repr(test_telescope)


def test_send_cmd(test_telescope):
    response = test_telescope.send_cmd("?")
    assert isinstance(response, str)


def test_help(test_telescope):
    test_telescope.help()


def test_clear_buffer(test_telescope):
    test_telescope.clear_buffer()


def test_read_ntrig(test_telescope):
    n = test_telescope.read_ntrig()
    assert isinstance(n, int) and n >= 0


def test_read_buffer(test_telescope):
    n = test_telescope.read_ntrig()
    trigs = test_telescope.read_buffer()

    assert isinstance(trigs, list)
    assert all(isinstance(t, int) for t in trigs)
    assert n == len(trigs)


def test_calibrate(test_telescope):
    assert not test_telescope.is_calibrated
    test_telescope.calibrate()
    assert test_telescope.is_calibrated
    assert test_telescope.position == (90.0, 0.0)


def test_move_to(test_telescope):
    with pytest.raises(Exception):
        test_telescope.move_to(0, 0)

    test_telescope.calibrate()
    test_telescope.move_to(0, 0)
    assert test_telescope.position == (0, 0)

    with pytest.raises(ValueError):
        test_telescope.move_to(-10, 0)
    with pytest.raises(ValueError):
        test_telescope.move_to(10, -50)


def test_reset_position(test_telescope):
    test_telescope.calibrate()
    test_telescope.move_to(0, 0)
    test_telescope.reset_position()
    assert not test_telescope.is_calibrated
    assert test_telescope.position == (60, 40)


def test_arduino_date(test_telescope):
    d = test_telescope.arduino_date
    assert isinstance(d, list)
    assert all(isinstance(x, int) for x in d)

    test_telescope.arduino_date = [2026, 1, 24, 20, 19, 0]
