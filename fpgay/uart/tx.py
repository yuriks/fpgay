from nmigen import *

from .baud_generator import BaudGenerator


class Tx(Elaboratable):
    def __init__(self, clk_freq, baud=115200, data_bits=8, stop_bits=1):
        self.clk_freq = clk_freq
        self.baud = baud
        self.data_bits = data_bits
        self.stop_bits = stop_bits

        self.i_data = Signal(data_bits)
        self.i_start = Signal()

        self.o_serial_tx = Signal(reset=1)
        self.o_busy = Signal(reset=True)

    def elaborate(self, platform):
        m = Module()

        baudgen = BaudGenerator(self.clk_freq, self.baud)
        m.submodules += baudgen

        data_reg = Signal.like(self.i_data)

        with m.FSM(reset='idle') as fsm:
            with m.State('idle'):
                m.d.comb += self.o_busy.eq(False)
                with m.If(self.i_start):
                    m.d.comb += baudgen.i_reset.eq(1)
                    m.d.sync += data_reg.eq(self.i_data)
                    m.next = 'start'
            with m.State('start'):
                m.d.comb += self.o_serial_tx.eq(0)
                with m.If(baudgen.o_tick):
                    m.next = ('transmit', 0)
            for i in range(self.data_bits):
                with m.State(('transmit', i)):
                    m.d.comb += self.o_serial_tx.eq(data_reg[0])
                    with m.If(baudgen.o_tick):
                        m.d.sync += data_reg.eq(data_reg >> 1)
                        if i == self.data_bits - 1:
                            m.next = ('stop', 0)
                        else:
                            m.next = ('transmit', i + 1)
            for i in range(self.stop_bits):
                with m.State(('stop', i)):
                    with m.If(baudgen.o_tick):
                        if i == self.stop_bits - 1:
                            m.next = 'idle'
                        else:
                            m.next = ('stop', i + 1)

        return m
