from manim import *

# /animate-anything LaTeX golden — "1/2 + 1/4 + 1/8 + … = 1" via TransformMatchingTex (needs LaTeX).
config.background_color = "#333333"   # the 3b1b warm-grey canvas

class GeometricSeries(Scene):
    def construct(self):
        title = MathTex(r"\frac{1}{2}+\frac{1}{4}+\frac{1}{8}+\cdots", color=BLUE_C).to_edge(UP)
        self.play(Write(title))
        self.wait()

        # A unit bar = "1" (the given → neutral).
        bar = Rectangle(width=6, height=0.8, color=WHITE).set_stroke(width=2)
        one = MathTex("1", color=GREY_BROWN).next_to(bar, LEFT)
        self.play(Create(bar), Write(one))
        self.wait()

        colors = [BLUE_D, GREEN, YELLOW, GOLD]
        sums = [r"\tfrac{1}{2}", r"\tfrac{1}{2}+\tfrac{1}{4}",
                r"\tfrac{1}{2}+\tfrac{1}{4}+\tfrac{1}{8}",
                r"\tfrac{1}{2}+\tfrac{1}{4}+\tfrac{1}{8}+\tfrac{1}{16}"]
        running = MathTex(r"=\,?", color=YELLOW).next_to(bar, DOWN, buff=0.6)
        self.play(FadeIn(running, shift=UP * 0.2))

        left = -3.0
        for k in range(4):                       # fill halves: each term shrinks by 1/2
            w = 6 * (0.5 ** (k + 1))
            seg = Rectangle(width=w, height=0.8, color=colors[k]).set_fill(colors[k], 0.6).set_stroke(width=1)
            seg.move_to([left + w / 2, bar.get_y(), 0])
            left += w
            new = MathTex(r"=\," + sums[k], color=YELLOW).next_to(bar, DOWN, buff=0.6)
            self.play(Create(seg), TransformMatchingTex(running, new), run_time=1.2)  # the morph
            running = new
            self.wait(0.5)

        # The aha: the halves fill the whole bar → the sum IS 1 (resolved → gold).
        final = MathTex(r"=\,1", color=GOLD).scale(1.2).next_to(bar, DOWN, buff=0.6)
        self.play(ReplacementTransform(running, final), Indicate(bar, color=GOLD), run_time=1.6)
        self.wait(2)
