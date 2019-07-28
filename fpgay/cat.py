from nmigen import *
from nmigen_boards.ice40_hx8k_b_evn import ICE40HX8KBEVNPlatform
from .uart import Tx, Rx


class CatFoo(Elaboratable):
    def elaborate(self, platform):
        clk = platform.request("clk12")
        clk_freq = platform.get_clock_constraint(clk)

        leds = Cat(platform.request("user_led", i) for i in range(8))
        tx_act_led = leds[0]
        rx_act_led = leds[1]
        rx_err_led = leds[7]

        uart_pins = platform.request("uart", 0)

        m = Module()
        m.domains.sync = ClockDomain()
        m.d.comb += ClockSignal().eq(clk.i)

        tx = Tx(clk_freq, baud=115200)
        m.submodules += tx
        rx = Rx(clk_freq, baud=115200)
        m.submodules += rx

        send_interval = int(clk_freq / 10)
        ctr = Signal(max=send_interval)

        stored_char = Signal(8, reset=ord('~'))

        m.d.comb += (
            tx_act_led.eq(tx.o_busy),
            uart_pins.tx.eq(tx.o_serial_tx),

            rx_act_led.eq(rx.o_busy),
            rx_err_led.eq(rx.o_receive_error | rx.o_overflow),
            rx.i_serial_rx.eq(uart_pins.rx)
        )

        with m.If(~tx.o_busy):
            m.d.sync += ctr.eq(ctr + 1)
            with m.If(ctr == 0):
                m.d.comb += tx.i_data.eq(stored_char), tx.i_start.eq(True)

        with m.If(rx.o_ready & (ctr == 0)):
            m.d.sync += stored_char.eq(rx.o_data)
            m.d.comb += rx.i_ack.eq(1)

        return m


if __name__ == "__main__":
    platform = ICE40HX8KBEVNPlatform()
    platform.build(CatFoo(), do_program=True)
