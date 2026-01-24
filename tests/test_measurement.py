"""Test the measurement convenience functions."""

import json
import os
import time

import pytest

from mumasp.measurement import measure, raster_scan, scan

from .fixtures import tempdir, test_telescope


def test_measure(test_telescope):
    test_telescope.calibrate()
    t0 = time.time()
    t_start, t_elapsed, trigs = measure(
        test_telescope,
        max_t_s=3,
        read_interval_s=1,
    )
    assert time.time() - t0 < 4

    assert isinstance(t_start, float)
    assert isinstance(t_elapsed, float) and t_elapsed < 4
    assert isinstance(trigs, list) and all(isinstance(t, int) for t in trigs)


def test_scan(test_telescope, tempdir):
    test_telescope.calibrate()
    t0 = time.time()
    scan(
        test_telescope,
        positions=[(0, 10), (45, 20)],
        save_dir=os.path.join(tempdir.name, "testrun"),
        max_t_s=3,
        read_interval_s=1,
        skip_existing=False,
    )

    assert time.time() - t0 < 7

    log_path = os.path.join(
        tempdir.name,
        "testrun",
        "mumasp.log",
    )
    f1_path = os.path.join(
        tempdir.name,
        "testrun",
        "meas_t0.00_p10.00.txt",
    )
    f2_path = os.path.join(
        tempdir.name,
        "testrun",
        "meas_t45.00_p20.00.txt",
    )
    assert os.path.exists(log_path)
    assert os.path.exists(f1_path)
    assert os.path.exists(f2_path)

    with open(f1_path) as f:
        d1 = json.loads(f.readline())
        ts1 = f.readlines()
    with open(f2_path) as f:
        d2 = json.loads(f.readline())
        ts2 = f.readlines()

    assert d1["theta_deg"] == 0 and d1["phi_deg"] == 10
    assert len(ts1) > 1
    assert d2["theta_deg"] == 45 and d2["phi_deg"] == 20
    assert len(ts2) > 1


def test_raster_scan(test_telescope, tempdir):
    thetas = [0, 45, 90]
    phis = [0, 30, 60, 90]

    test_telescope.calibrate()
    t0 = time.time()
    raster_scan(
        test_telescope,
        thetas=thetas,
        phis=phis,
        save_dir=os.path.join(tempdir.name, "testrun"),
        max_t_s=2,
        read_interval_s=1,
        skip_existing=False,
    )

    assert time.time() - t0 < 3 * len(thetas) * len(phis)

    starts = []
    for t, p in zip(thetas, phis):
        fpath = os.path.join(
            tempdir.name,
            "testrun",
            f"meas_t{t:.2f}_p{p:.2f}.txt",
        )
        assert os.path.exists(fpath)

        with open(fpath) as f:
            starts.append(json.loads(f.readline())["t_start_s"])

    # Now repeat with skip_existing = True
    t0 = time.time()
    raster_scan(
        test_telescope,
        thetas=thetas,
        phis=phis,
        save_dir=os.path.join(tempdir.name, "testrun"),
        max_t_s=2,
        read_interval_s=1,
        skip_existing=True,
    )

    assert time.time() - t0 < 1

    # Test if files are the same
    for t, p, s in zip(thetas, phis, starts):
        fpath = os.path.join(
            tempdir.name,
            "testrun",
            f"meas_t{t:.2f}_p{p:.2f}.txt",
        )
        assert os.path.exists(fpath)

        with open(fpath) as f:
            s == json.loads(f.readline())["t_start_s"]
