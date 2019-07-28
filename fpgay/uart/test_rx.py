import pytest
from nmigen import *
from nmigen.back import pysim
from nmigen.hdl.ast import Delay

from .rx import Rx


def test_receive():
    baud = 1200
    clk_freq = baud * 8
    baud_period = 1 / baud

    rx = Rx(clk_freq, baud, data_bits=7, stop_bits=2)

    with pysim.Simulator(rx) as sim:
        sim.add_clock(1 / clk_freq)

        def fn():
            yield Delay(2.5e-5)

            bits = [
                0,  # Start bit
                1, 0, 1, 1, 0, 0, 1,  # Data bits
                1, 1,  # Stop bits
            ]
            for bit in bits:
                yield rx.i_serial_rx.eq(bit)
                yield Delay(baud_period)

            assert (yield rx.o_ready)
            assert (yield rx.o_data) == 0b1001101

            yield rx.i_ack.eq(True)
            yield Delay(1 / clk_freq)
            yield rx.i_ack.eq(False)
            assert not (yield rx.o_ready)

        sim.add_process(fn())
        sim.run()
