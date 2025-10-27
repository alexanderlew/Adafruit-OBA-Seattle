from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time

# ---------- Configuration ----------
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'
options.gpio_slowdown = 4   # Adjust up if flickering (try 5)
options.pwm_bits = 5        # Reduce to 4 for smoother but lower color depth
options.brightness = 60     # Start at 60%, lower if flicker worsens
matrix = RGBMatrix(options=options)

canvas = matrix.CreateFrameCanvas()
font = graphics.Font()
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/6x10.bdf")

# ---------- Helper Functions ----------
def fill_color(r, g, b, duration=2):
    """Fill screen with solid color for a few seconds."""
    canvas.Fill(r, g, b)
    matrix.SwapOnVSync(canvas)
    time.sleep(duration)

def show_static_text(text="STATIC TEST", duration=3):
    """Display static text centered."""
    canvas.Clear()
    color = graphics.Color(255, 255, 0)
    text_length = graphics.DrawText(canvas, font, 10, 18, color, text)
    matrix.SwapOnVSync(canvas)
    time.sleep(duration)

def scroll_text(text="MOVING TEXT TEST", speed=0.03):
    """Scroll text horizontally across the screen."""
    color = graphics.Color(0, 200, 255)
    pos = canvas.width
    for _ in range(0, canvas.width * 2):
        canvas.Clear()
        graphics.DrawText(canvas, font, pos, 18, color, text)
        pos -= 1
        if pos + len(text) * 6 < 0:
            pos = canvas.width
        matrix.SwapOnVSync(canvas)
        time.sleep(speed)

# ---------- Test Sequence ----------
try:
    while True:
        # Solid color tests
        fill_color(255, 0, 0)    # Red
        fill_color(0, 255, 0)    # Green
        fill_color(0, 0, 255)    # Blue
        fill_color(255, 255, 255)# White

        # Static text test
        show_static_text("STATIC TEST", 3)

        # Scrolling text test
        scroll_text("MOVING TEXT TEST", 0.03)

except KeyboardInterrupt:
    canvas.Clear()
    matrix.SwapOnVSync(canvas)
    print("\nExiting flicker test.")
