from manim import *

# /animate-anything golden example — "1+3+5+…+(2n-1) = n²", the classic 3b1b visual proof.
config.background_color = "#333333"   # the warm-grey canvas

class OddSquares(Scene):
    def construct(self):
        title = Text("1 + 3 + 5 + 7 = ?", color=BLUE_C).to_edge(UP)
        self.play(Write(title))
        self.wait()

        # Build an n×n grid one L-shaped "odd" layer at a time (color encodes each odd number).
        n = 4
        layer_colors = [BLUE_D, GREEN, YELLOW, GOLD]
        cells, groups = VGroup(), []
        for k in range(n):                       # layer k adds the (2k+1) new cells forming an L
            layer = VGroup()
            for i in range(k + 1):               # bottom row of the L
                layer += Square(0.7).move_to([i - 1.5, -k + 1.0, 0])
            for j in range(k):                   # left column of the L
                layer += Square(0.7).move_to([k - 1.5, j - k + 2.0, 0])
            layer.set_stroke(WHITE, 2).set_fill(layer_colors[k], 0.55)
            groups.append(layer)

        odd_labels = ["1", "+3", "+5", "+7"]
        running = None
        for k, layer in enumerate(groups):
            lbl = Text(odd_labels[k], color=layer_colors[k]).scale(0.8).to_edge(DOWN).shift(RIGHT * (k * 0.8 - 1.2))
            self.play(LaggedStart(*[Create(sq) for sq in layer], lag_ratio=0.15), FadeIn(lbl, shift=UP * 0.2))
            cells += layer
            self.wait(0.6)

        # The aha: those L-layers ARE a 4×4 square. Morph the labels into "= 4²" and pulse the grid.
        answer = Text("= 4 × 4 = 16", color=GOLD).scale(0.9).to_edge(DOWN)
        self.play(ReplacementTransform(title.copy(), answer), Indicate(cells, color=GOLD, scale_factor=1.05), run_time=1.6)
        self.wait(2)
