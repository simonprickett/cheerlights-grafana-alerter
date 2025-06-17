import json
import network
import secrets
import time

from picographics import PicoGraphics
from umqtt.robust import MQTTClient

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

# Connect to the network.
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD) 

while not wlan.isconnected() and wlan.status() >= 0:
    print("Connecting to wifi...")
    time.sleep(1)

ip_address = wlan.ifconfig()[0]
print(f"Connected with IP address {ip_address}")


def clear_display():
    display.set_pen(PENS["black"])
    display.clear()
    unicorn.update(display)

def show_current_color(color_name):
    display.set_pen(PENS[color_name])
    display.rectangle(CURRENT_COLOR_X, CURRENT_COLOR_Y, CURRENT_COLOR_BLOCK_SIZE, CURRENT_COLOR_BLOCK_SIZE)
    unicorn.update(display)

def show_previous_colors(color_names):
    x = 0
    y = 0

    # Initially go across the top of the display left to right.
    x_incr = PREVIOUS_COLOR_BLOCK_SIZE
    y_incr = 0

    for counter, color_name in enumerate(color_names):
        try:
            display.set_pen(PENS[color_name])
        except KeyError:
            display.set_pen(PENS["black"])
            print(f"Bad color name: {color_name}")

        display.rectangle(x, y, PREVIOUS_COLOR_BLOCK_SIZE, PREVIOUS_COLOR_BLOCK_SIZE)
        unicorn.update(display)
        time.sleep(0.5)

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


def msg_receiver(topic, msg):
    global recent_colors

    json_data = json.loads(msg.decode("utf-8"))

    try:
        latest_alert_starts_at = 0
        latest_alert_index = -1

        for idx, alert in enumerate(json_data["alerts"]):
            starts_at = alert["startsAt"]

            if starts_at > latest_alert_starts_at:
                print(f"Found new latest alert at {idx}:")
                print(alert)
                latest_alert_starts_at = starts_at
                latest_alert_index = idx
            else:
                print(f"Ignoring older alert that starts at {starts_at}")

        new_color = json_data['alerts'][latest_alert_index]['labels']['color']
        print(f"Latest color: {new_color}")

        recent_colors.insert(0, new_color)

        # Trim the list if needed.
        recent_colors = recent_colors[:TOTAL_COLOR_BLOCKS]

        show_current_color(recent_colors[0])
        show_previous_colors(recent_colors[1:])

    except Exception:
        print("Bad message received:")
        print(json_data)


unicorn.set_brightness(0.4)
clear_display()

print(f"Connecting to {secrets.MQTT_BROKER}:{secrets.MQTT_PORT}")
client = MQTTClient(secrets.MQTT_CLIENT_NAME, secrets.MQTT_BROKER, secrets.MQTT_PORT) # TODO remove hard coded client ID.
client.DEBUG = True
client.set_callback(msg_receiver)
client.connect()
print(f"Subscribing to topic...")
client.subscribe(secrets.MQTT_TOPIC)
#client.subscribe(b"simongrafana/cheerlights")
print("Waiting for messages.")

while True:
    # If we had something else to do we could replace this with
    # a sleep loop and client.check_msg()
    #client.wait_msg()
    try:
        client.check_msg()
        time.sleep(1)
        print(f"alive {time.ticks_ms()}")
    except Exception as e:
        print("Something went wrong!")
        print(e)

    
