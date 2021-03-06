from migen import *
from migen.build.generic_platform import Pins
from migen.build.platforms import icebreaker

class RGBFadeGamma(Module):
    def __init__(self, leds):
        pwm_width = 16
        fade_width = 8
        ctr_width = 28

        ctr = Signal(ctr_width)
        col = Signal(3)
        direction = Signal()
        fade = Signal(fade_width)
        self.comb += col.eq(ctr[ctr_width-3:ctr_width])
        self.comb += direction.eq(ctr[ctr_width-4])
        self.comb += fade.eq(ctr[ctr_width-4-fade_width:ctr_width-4])

        fade_corr = Signal(pwm_width)
        r_val = Signal(pwm_width)
        g_val = Signal(pwm_width)
        b_val = Signal(pwm_width)
        pwm_r = Signal()
        pwm_g = Signal()
        pwm_b = Signal()
        pwm_ctr = Signal(pwm_width)

        # Gamma correction
        self.specials.mem = Memory(16, 256, init=self.gen_gamma_table(256))
        p = self.mem.get_port()
        self.specials += p
        self.comb += p.adr.eq(fade)
        self.comb += fade_corr.eq(p.dat_r)

        # Fading up and down for each combination of colours
        self.sync += ctr.eq(ctr + 1)
        self.sync += r_val.eq(Mux(col[0], Mux(direction, ~fade_corr, fade_corr), 0))
        self.sync += g_val.eq(Mux(col[1], Mux(direction, ~fade_corr, fade_corr), 0))
        self.sync += b_val.eq(Mux(col[2], Mux(direction, ~fade_corr, fade_corr), 0))

        # PWM
        self.sync += pwm_ctr.eq(pwm_ctr + 1)
        self.sync += pwm_r.eq(pwm_ctr < r_val)
        self.sync += pwm_g.eq(pwm_ctr < g_val)
        self.sync += pwm_b.eq(pwm_ctr < b_val)
        self.specials += Instance("SB_RGBA_DRV",
                i_CURREN=1,
                i_RGBLEDEN=1,
                i_RGB0PWM=pwm_r,
                i_RGB1PWM=pwm_g,
                i_RGB2PWM=pwm_b,
                o_RGB0=leds[0],
                o_RGB1=leds[1],
                o_RGB2=leds[2],
                p_CURRENT_MODE="0b1",
                p_RGB0_CURRENT="0b000001",
                p_RGB1_CURRENT="0b000001",
                p_RGB2_CURRENT="0b000001",
        )

    def gen_gamma_table(self, n):
        gamma = 2.2
        return [int(0xFFFF * pow((1.0 / 255.0) * i, gamma)) for i in range(n)]

rgb_led = [
     ("red",   0, Pins("39")),
     ("green", 0, Pins("40")),
     ("blue",  0, Pins("41")),
]

plat = icebreaker.Platform()
plat.add_extension(rgb_led)
leds = [plat.request(led) for led in ["red", "green", "blue"]]
rgb_fade = RGBFadeGamma(leds)
plat.build(rgb_fade)
plat.create_programmer().flash(0, 'build/top.bin')
