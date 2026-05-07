# core/tools.py

import datetime
import platform
import psutil


def get_time():
    now = datetime.datetime.now()
    return now.strftime("It is %I:%M %p.")


def get_date():
    today = datetime.date.today()
    return today.strftime("Today is %B %d, %Y.")


def get_battery():
    battery = psutil.sensors_battery()
    if battery is None:
        return "I cannot detect battery on this device."
    return f"Battery is at {battery.percent} percent."


def get_system_info():
    return f"You are running {platform.system()} {platform.release()}."
