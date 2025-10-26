# ==========================
# oba-matrix.py
# ==========================
# Non-scrolling 2-arrivals static display for Adafruit RGB LED Matrix (64x32)
# Header: "Rte Dest Min" using smaller font
# Fully left-justified route
# Arrivals 2 pixels below header
# Time (HH:MM) at bottom row
# Compatible with Pi 1 B+, Python 3
# ==========================

import time
import requests
from datetime import datetime
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# ==========================
# Configurable abbreviations
# ==========================
DEST_ABBREVIATIONS = {
    "Station": "Sta",
    "University": "Univ",
    "Center": "Ctr",
    "Terminal": "Term",
    "Park & Ride": "P&R",
    "Seattle": "SEA",
    "Tacoma Dome": "T Dome",
    "Lynnwood City Center": "Lynnwood",
    "Lake": "Lk",
    "Federal Way": "Fed Way"
}

ROUTE_ABBREVIATIONS = {
    "1 Line": "1",
    # add more as needed
}

MAX_DEST_CHARS = 12  # max characters for destination

# ==========================
# OneBusAway API configuration
# ==========================
OBA_API_KEY = "TEST"
STOP_IDS = ["40_99603", "40_99610"]

# ==========================
# Abbreviation helpers
# ==========================
def abbreviate_destination(dest, max_chars=MAX_DEST_CHARS):
    if not dest:
        return ""
    for full, abbr in DEST_ABBREVIATIONS.items():
        dest = dest.replace(full, abbr)
    if len(dest) > max_chars:
        dest = dest[:max_chars]
    return dest

def abbreviate_route(route):
    return ROUTE_ABBREVIATIONS.get(route, route)

# ==========================
# Fetch arrivals from OneBusAway
# ==========================
def get_arrivals_from_oba():
    arrivals = []
    for stop_id in STOP_IDS:
        url = "https://api.pugetsound.onebusaway.org/api/where/arrivals-and-departures-for-stop/{0}.json?key={1}".format(
            stop_id, OBA_API_KEY
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print("Error fetching OBA data for stop {}: {}".format(stop_id, e))
            continue

        current_time = data.get("currentTime", 0)
        entries = data.get("data", {}).get("entry", {}).get("arrivalsAndDepartures", [])
        for a in entries:
            route = a.get("routeShortName") or a.get("routeId", "???")
            route = abbreviate_route(route)
            headsign = a.get("tripHeadsign", "Unknown")
            predicted = a.get("predictedArrivalTime") or a.get("scheduledArrivalTime")
            if not predicted:
                continue
            mins = int((predicted - current_time) / 60000)
            if mins >= 0:
                arrivals.append({
                    "route": route,
                    "headsign": headsign,
                    "mins": mins
                })

    arrivals.sort(key=lambda x: x['mins'])
    print("Arrivals fetched:", arrivals)
    return arrivals[:2]  # next 2 arrivals only

# ==========================
# Matrix initialization
# ==========================
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.brightness = 50
options.pwm_bits = 5
options.hardware_mapping = "adafruit-hat"
options.disable_hardware_pulsing = True
options.gpio_slowdown = 4  # good for Pi 1

matrix = RGBMatrix(options=options)
offscreen_canvas = matrix.CreateFrameCanvas()

# ==========================
# Load fonts
# ==========================
font_path = "/home/pi/rpi-rgb-led-matrix/fonts/5x8.bdf"
font = graphics.Font()
font.LoadFont(font_path)

header_font_path = "/home/pi/rpi-rgb-led-matrix/fonts/4x6.bdf"
headerFont = graphics.Font()
headerFont.LoadFont(header_font_path)

# Colors
arrivalColor = graphics.Color(255, 255, 0)      # yellow
headerColor = graphics.Color(0, 255, 255)       # cyan
timeColor = graphics.Color(255, 0, 0)           # red (same as HELLO test)

# ==========================
# Draw header
# ==========================
def draw_header(canvas):
    graphics.DrawText(canvas, headerFont, 1, 7, headerColor, "Rte Dest")
    min_text = "Min"
    min_width = graphics.DrawText(canvas, headerFont, 0, 0, headerColor, min_text)
    graphics.DrawText(canvas, headerFont, 64 - min_width - 1, 7, headerColor, min_text)

# ==========================
# Draw arrivals
# ==========================
def draw_arrivals(canvas, font, color, arrivals):
    line_height = 8  # 5x8 font
    left_margin = 1
    max_left_width = 64 - 12

    for i, a in enumerate(arrivals):
        # 2 pixels below bottom of header (header y=7, header height ~6)
        y = 7 + 6 + 2 + i * line_height
        dest = abbreviate_destination(a['headsign'])
        route = a['route']
        left_text = "{} {}".format(route, dest)

        # truncate if needed
        left_width = graphics.DrawText(canvas, font, 0, 0, color, left_text)
        if left_width > max_left_width:
            allowed_chars = int(len(left_text) * max_left_width / left_width)
            left_text = left_text[:allowed_chars]

        right_text = "{}".format(a['mins'])
        right_width = graphics.DrawText(canvas, font, 0, 0, color, right_text)
        right_x = 64 - right_width - 1

        graphics.DrawText(canvas, font, left_margin, y, color, left_text)
        graphics.DrawText(canvas, font, right_x, y, color, right_text)

# ==========================
# Draw time at bottom
# ==========================
def draw_time(canvas):
    now = datetime.now()
    time_text = now.strftime("%H:%M")
    # 1 pixel from bottom
    y = 32 - 1
    width = graphics.DrawText(canvas, font, 0, 0, timeColor, time_text)
    x = 64 - width - 1
    graphics.DrawText(canvas, font, x, y, timeColor, time_text)

# ==========================
# HELLO test
# ==========================
print("Running HELLO test...")
offscreen_canvas.Clear()
graphics.DrawText(offscreen_canvas, font, 2, 15, timeColor, "HELLO")
matrix.SwapOnVSync(offscreen_canvas)
time.sleep(2)
offscreen_canvas.Clear()
matrix.SwapOnVSync(offscreen_canvas)

# ==========================
# Main loop
# ==========================
while True:
    arrivals = get_arrivals_from_oba()
    offscreen_canvas.Clear()
    draw_header(offscreen_canvas)
    if arrivals:
        draw_arrivals(offscreen_canvas, font, arrivalColor, arrivals)
    else:
        print("No arrivals to display")
    draw_time(offscreen_canvas)
    
    # clear top row manually to remove stray pixels
    for x in range(64):
        offscreen_canvas.SetPixel(x, 0, 0, 0, 0)

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    time.sleep(30)
