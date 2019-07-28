from nmigen import *


class Rx(Elaboratable):
    def __init__(self, clk_freq, baud=115200, data_bits=8, stop_bits=1):
        self.clk_freq = clk_freq
        self.baud = baud
        self.divider = round(clk_freq / baud)
        assert self.divider >= 8
        self.data_bits = data_bits
        self.stop_bits = stop_bits

        self.i_serial_rx = Signal()
        self.i_ack = Signal()

        self.o_busy = Signal(reset=True)
        self.o_ready = Signal()
        self.o_overflow = Signal()
        self.o_receive_error = Signal()
        self.o_data = Signal(data_bits)

    def elaborate(self, platform):
        m = Module()

        phase_ctr = Signal(max=self.divider)
        with m.If(phase_ctr == 0):
            m.d.sync += phase_ctr.eq(self.divider - 1)
        with m.Else():
            m.d.sync += phase_ctr.eq(phase_ctr - 1)

        with m.If(self.i_ack):
            m.d.sync += (
                self.o_ready.eq(False),
                self.o_overflow.eq(False),
                self.o_receive_error.eq(False))

        with m.FSM(reset='idle') as fsm:
            with m.State('idle'):
                m.d.comb += self.o_busy.eq(False)
                with m.If(~self.i_serial_rx):
                    with m.If(self.o_ready):
                        m.d.sync += self.o_overflow.eq(True)
                    with m.Else():
                        m.d.sync += phase_ctr.eq(self.divider // 2 - 1)
                        m.next = 'start'
            with m.State('start'):
                with m.If(phase_ctr == 0):
                    with m.If(self.i_serial_rx != 0):
                        m.d.sync += self.o_receive_error.eq(True)
                        m.next = 'idle'
                    with m.Else():
                        m.next = ('transmit', 0)
            for i in range(self.data_bits):
                with m.State(('transmit', i)):
                    with m.If(phase_ctr == 0):
                        m.d.sync += self.o_data[i].eq(self.i_serial_rx)
                        if i == self.data_bits - 1:
                            m.next = ('stop', 0)
                        else:
                            m.next = ('transmit', i + 1)
            for i in range(self.stop_bits):
                with m.State(('stop', i)):
                    with m.If(phase_ctr == 0):
                        with m.If(self.i_serial_rx != 1):
                            m.d.sync += self.o_receive_error.eq(True)
                            m.next = 'idle'
                        with m.Else():
                            if i == self.stop_bits - 1:
                                m.d.sync += self.o_ready.eq(True)
                                m.next = 'idle'
                            else:
                                m.next = ('stop', i + 1)

        return m
