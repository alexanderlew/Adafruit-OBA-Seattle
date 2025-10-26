from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.brightness = 40
options.gpio_slowdown = 4

matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

font = graphics.Font()
font.LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/5x8.bdf")
color = graphics.Color(255, 255, 0)

graphics.DrawText(canvas, font, 1, 10, color, "HELLO 5x8")
graphics.DrawText(canvas, font, 1, 20, color, "WORKS OK")
matrix.SwapOnVSync(canvas)
time.sleep(10)
