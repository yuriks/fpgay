import pytest
from nmigen import *
from nmigen.back import pysim
from nmigen.hdl.ast import Delay

from .tx import Tx


def test_send():
    baud = 9600
    clk_freq = baud * 4
    baud_period = 1 / 9600

    tx = Tx(clk_freq, baud, data_bits=7, stop_bits=2)

    with pysim.Simulator(tx) as sim:
        sim.add_clock(1 / clk_freq)

        def fn():
            yield Delay(2.5e-5)

            yield tx.i_data.eq(0b1001101)
            yield tx.i_start.eq(True)

            yield Delay(baud_period / 2)

            bits = [
                0,  # Start bit
                1, 0, 1, 1, 0, 0, 1,  # Data bits
                1, 1,  # Stop bits
            ]
            for bit in bits:
                assert (yield tx.o_serial_tx) == bit
                assert (yield tx.o_busy)
                yield Delay(baud_period)

            assert (yield tx.o_serial_tx) == 1
            assert not (yield tx.o_busy)

        sim.add_sync_process(fn())
        sim.run()
