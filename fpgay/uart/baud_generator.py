from nmigen import *


class BaudGenerator(Elaboratable):
    def __init__(self, clk_freq, baud, ctr_width=16):
        assert clk_freq > baud

        self.ctr_increment = round((baud << ctr_width) / clk_freq)
        self.ctr = Signal(ctr_width)

        self.i_reset = Signal()
        self.o_tick = Signal()

    def elaborate(self, platform):
        m = Module()
        m.d.sync += Cat(self.ctr, self.o_tick).eq(
            Mux(self.i_reset, 0, self.ctr + self.ctr_increment))
        return m
