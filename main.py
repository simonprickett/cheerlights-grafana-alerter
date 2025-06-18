import asyncio
import json
import secrets

from picographics import PicoGraphics
from mqtt_as import MQTTClient, config

try:
    from stellar import StellarUnicorn as Unicorn
    from picographics import DISPLAY_STELLAR_UNICORN as DISPLAY
except ImportError:
    from cosmic import CosmicUnicorn as Unicorn
    from picographics import DISPLAY_COSMIC_UNICORN as DISPLAY

unicorn = Unicorn()

display = PicoGraphics(DISPLAY)
DISPLAY_WIDTH = Unicorn.WIDTH
DISPLAY_HEIGHT = Unicorn.HEIGHT

PENS = {
    "black": display.create_pen(0, 0, 0),
    "red": display.create_pen(255, 0, 0),
    "green": display.create_pen(0, 128, 0),
    "blue": display.create_pen(0, 0, 255),
    "cyan": display.create_pen(0, 255, 255),
    "white": display.create_pen(255, 255, 255),
    "oldlace": display.create_pen(253, 245, 230),
    "purple": display.create_pen(128, 0, 128),
    "magenta": display.create_pen(255, 0, 255),
    "yellow": display.create_pen(255, 255, 0),
    "orange": display.create_pen(255, 165, 0),
    "pink": display.create_pen(255, 192, 203)
}

TOTAL_COLOR_BLOCKS = 13
PREVIOUS_COLORS_PER_ROW = 4
PREVIOUS_COLOR_BLOCK_SIZE = DISPLAY_WIDTH // PREVIOUS_COLORS_PER_ROW
CURRENT_COLOR_BLOCK_SIZE = DISPLAY_WIDTH - (2 * PREVIOUS_COLOR_BLOCK_SIZE) - 2
CURRENT_COLOR_X = PREVIOUS_COLOR_BLOCK_SIZE + 1
CURRENT_COLOR_Y = CURRENT_COLOR_X
MAX_X = PREVIOUS_COLOR_BLOCK_SIZE * (PREVIOUS_COLORS_PER_ROW - 1)
MAX_Y = PREVIOUS_COLOR_BLOCK_SIZE * (PREVIOUS_COLORS_PER_ROW - 1)

recent_colors = []

# Configure MQTT library
config["ssid"] = secrets.WIFI_SSID
config["wifi_pw"] = secrets.WIFI_PASSWORD
config["server"] = secrets.MQTT_BROKER
config["queue_len"] = 1

latest_entry_id = 0

def clear_display():
    display.set_pen(PENS["black"])
    display.clear()
    unicorn.update(display)

def show_current_color(color_name):
    display.set_pen(PENS[color_name])
    display.rectangle(CURRENT_COLOR_X, CURRENT_COLOR_Y, CURRENT_COLOR_BLOCK_SIZE, CURRENT_COLOR_BLOCK_SIZE)
    unicorn.update(display)

async def show_previous_colors(color_names):
    x = 0
    y = 0

    # Initially go across the top of the display left to right.
    x_incr = PREVIOUS_COLOR_BLOCK_SIZE
    y_incr = 0

    for color_name in color_names:
        try:
            display.set_pen(PENS[color_name])
        except KeyError:
            display.set_pen(PENS["black"])
            print(f"Bad color name: {color_name}")

        display.rectangle(x, y, PREVIOUS_COLOR_BLOCK_SIZE, PREVIOUS_COLOR_BLOCK_SIZE)
        unicorn.update(display)
        await asyncio.sleep(0.5)

        if x == MAX_X:
            # Go down the right of the display now.
            x_incr = 0
            y_incr = PREVIOUS_COLOR_BLOCK_SIZE

        if y == MAX_Y:
            # Go across the bottom of the display now, right to left.
            x_incr = 0 - PREVIOUS_COLOR_BLOCK_SIZE
            y_incr = 0

        if x == 0 and y == MAX_Y: 
            # Go up the left side of the display now.
            x_incr = 0
            y_incr = 0 - PREVIOUS_COLOR_BLOCK_SIZE

        x = x + x_incr
        y = y + y_incr


async def messages(client):
    global recent_colors, latest_entry_id

    async for topic, msg, retained in client.queue:
        json_data = json.loads(msg.decode("utf-8"))

        try:
            sorted_alerts = sorted(json_data["alerts"], key=lambda a: a["labels"]["entryId"])
            print(sorted_alerts)
            for alert in sorted_alerts:
                entry_id = int(alert["labels"]["entryId"])

                # Find newer firing alerts that are named cheerlights-updated.
                if (entry_id > latest_entry_id) and alert["status"] == "firing" and alert["labels"]["alertname"] == "cheerlights-updated":
                    print("Found new firing cheerlights-updated alert:")
                    print(alert)
                    latest_entry_id = entry_id

                    new_color = alert["labels"]["color"]
                    print(f"Latest color: {new_color}")

                    recent_colors.insert(0, new_color)

                    # Trim the list if needed.
                    recent_colors = recent_colors[:TOTAL_COLOR_BLOCKS]

                    show_current_color(recent_colors[0])
                    await show_previous_colors(recent_colors[1:])

                else:
                    print("Ignoring this alert:")
                    print(alert)
                    
                    if entry_id <= latest_entry_id:
                        print("Reason: entry_id <= latest_entry_id")
                    if alert["status"] != "firing":
                        print(f"Reason: status was {alert['status']}")
                    if alert["labels"]["alertname"] != "cheerlights-updated":
                        print(f"Reason: alertname was {alert['labels']['alertname']}")
                    
        except Exception:
            print("Bad message received:")
            print(json_data)

async def up(client):
    while True:
        await client.up.wait()
        client.up.clear()
        print(f"Subscribing to topic: {secrets.MQTT_TOPIC}")
        await client.subscribe(secrets.MQTT_TOPIC, 1)

async def main(client):
    await client.connect()
    for coroutine in (up, messages):
        asyncio.create_task(coroutine(client))

    while True:
        await asyncio.sleep(5)
        # TODO other stuff?
        print("ok")


unicorn.set_brightness(0.4)
clear_display()

MQTTClient.DEBUG = True
client = MQTTClient(config)

try:
    asyncio.run(main(client))
finally:
    client.close()
