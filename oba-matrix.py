# ==========================
# nextbus-matrix.py
# ==========================
# Static OneBusAway display for Adafruit RGB LED Matrix (64x32)
# Fetches top arrivals, abbreviates long destinations, and displays them
# left-justified route + destination, right-justified minutes.
# Requires: rgbmatrix library (hzeller/rpi-rgb-led-matrix) and requests
# ==========================

import time
import requests
import os
from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Optional: keep if your repo uses prediction functions
from predict import predict

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
}

MAX_DEST_LENGTH = 12  # maximum characters for destination

# ==========================
# OneBusAway API configuration
# ==========================
OBA_API_KEY = "YOUR_KEY_HERE"  # replace with your OBA key
# OneBusAway stop IDs (you can add as many as you want)
STOP_IDS = ["1_75403", "1_12345"]  # replace with your actual stop IDs

# ==========================
# Abbreviation helper
# ==========================
def abbreviate_destination(dest):
    if not dest:
        return ""
    # Apply replacements
    for full, abbr in DEST_ABBREVIATIONS.items():
        dest = dest.replace(full, abbr)
    # Truncate intelligently
    if len(dest) > MAX_DEST_LENGTH:
        if " " in dest[:MAX_DEST_LENGTH]:
            dest = dest[:MAX_DEST_LENGTH].rsplit(" ", 1)[0]
        else:
            dest = dest[:MAX_DEST_LENGTH]
    return dest

# ==========================
# Fetch arrivals from OneBusAway
# ==========================
def get_arrivals_from_oba():
    all_arrivals = []
    now_ms = int(time.time() * 1000)

    for stop_id in STOP_IDS:
        url = f"https://api.pugetsound.onebusaway.org/api/where/arrivals-and-departures-for-stop/{stop_id}.json?key={OBA_API_KEY}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"OBA fetch error for stop {stop_id}:", e)
            continue

        for a in data["data"]["entry"]["arrivalsAndDepartures"]:
            arrival_time = a.get("predictedArrivalTime") or a.get("scheduledArrivalTime")
            if not arrival_time:
                continue
            minutes = int((arrival_time - now_ms) / 60000)
            if minutes < 0:
                continue
            all_arrivals.append({
                "routeShortName": a.get("routeShortName", ""),
                "tripHeadsign": a.get("tripHeadsign", ""),
                "minutes": minutes
            })

    # Sort combined list by minutes ascending
    all_arrivals.sort(key=lambda x: x["minutes"])
    return all_arrivals


# ==========================
# Draw arrivals on matrix
# ==========================
def draw_arrivals(canvas, font, color, arrivals):
    canvas.Clear()
    line_height = 10
    left_margin = 2

    for i, a in enumerate(arrivals[:3]):  # show top 3 arrivals
        y = (i + 1) * line_height
        dest = abbreviate_destination(a['tripHeadsign'])
        left_text = f"{a['routeShortName']} {dest}"
        right_text = f"{a['minutes']} min"

        # right-align minutes
        right_width = graphics.DrawText(canvas, font, 0, 0, color, right_text)
        right_x = 64 - right_width - 1

        # draw left and right text
        graphics.DrawText(canvas, font, left_margin, y, color, left_text)
        graphics.DrawText(canvas, font, right_x, y, color, right_text)

# ==========================
# Matrix initialization
# ==========================
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.brightness = 20       # lower = less power draw
options.gpio_slowdown = 2     # helps reduce flicker

matrix = RGBMatrix(options=options)
offscreen_canvas = matrix.CreateFrameCanvas()

# Load font
font_path = "/home/pi/rpi-rgb-led-matrix/fonts/7x13.bdf"  # adjust path if needed
font = graphics.Font()
font.LoadFont(font_path)

# Text color
textColor = graphics.Color(255, 255, 0)

# ==========================
# Main loop
# ==========================
while True:
    arrivals = get_arrivals_from_oba()
    draw_arrivals(offscreen_canvas, font, textColor, arrivals)
    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    time.sleep(30)  # refresh every 30 seconds
