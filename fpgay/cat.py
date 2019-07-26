from nmigen import *
from nmigen_boards.ice40_hx8k_b_evn import ICE40HX8KBEVNPlatform
from .uart import Tx


class CatFoo(Elaboratable):
    def elaborate(self, platform):
        clk = platform.request("clk12")
        clk_freq = platform.get_clock_constraint(clk)
        act_led = platform.request("user_led", 0)
        uart_pins = platform.request("uart", 0)

        m = Module()
        m.domains.sync = ClockDomain()
        m.d.comb += ClockSignal().eq(clk.i)

        tx = Tx(clk_freq, baud=115200)
        m.submodules += tx

        send_interval = int(clk_freq / 10)
        ctr = Signal(max=send_interval)

        m.d.comb += (
            act_led.eq(tx.o_busy),
            uart_pins.tx.eq(tx.o_serial_tx),
        )

        with m.If(~tx.o_busy):
            m.d.sync += ctr.eq(ctr + 1)
            with m.If(ctr == 0):
                m.d.comb += tx.i_data.eq(ord('A')), tx.i_start.eq(True)

        return m


if __name__ == "__main__":
    platform = ICE40HX8KBEVNPlatform()
    platform.build(CatFoo(), do_program=True)