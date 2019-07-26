import pytest
from nmigen import *
from nmigen.back import pysim
from .baud_generator import BaudGenerator


def relative_error(expected, actual):
    return abs(1 - actual / expected)


def test_precision():
    clk_freq = 25000
    baud = 9600
    baudgen = BaudGenerator(clk_freq, baud)

    test_duration = 1.0
    recorded_ticks = 0

    with pysim.Simulator(baudgen) as sim:
        sim.add_clock(1 / clk_freq)

        def fn():
            nonlocal recorded_ticks
            while True:
                if (yield baudgen.o_tick):
                    recorded_ticks += 1
                yield

        sim.add_sync_process(fn())
        sim.run_until(test_duration)

    recorded_baud = recorded_ticks / test_duration
    error = relative_error(baud, recorded_baud)

    print("Got {} out of {} (err {:.3}%)"
          .format(recorded_baud, baud, 100 * error))
    assert error < 1e-3
