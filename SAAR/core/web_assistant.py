# core/web_assistant.py
import webbrowser
import subprocess
import urllib.parse

class WebAssistant:
    def __init__(self):
        pass

    def track_package(self, tracking_number: str):
        # Universal tracking website
        url = f"https://parcelsapp.com/en/tracking/{tracking_number}"
        webbrowser.open(url)
        return f"Opening package tracking for {tracking_number} Sagar."

    def order_food(self, food_item: str):
        # Open Zomato search (assuming India context as default)
        query = urllib.parse.quote(food_item)
        url = f"https://www.zomato.com/search?q={query}"
        webbrowser.open(url)
        return f"Opening Zomato to search for {food_item} Sagar."

    def search_hotel(self, location: str):
        query = urllib.parse.quote(location)
        url = f"https://www.booking.com/searchresults.en-gb.html?ss={query}"
        webbrowser.open(url)
        return f"Opening Booking.com for hotels in {location} Sagar."

    def shop_online(self, item: str):
        query = urllib.parse.quote(item)
        url = f"https://www.amazon.in/s?k={query}"
        webbrowser.open(url)
        return f"Opening Amazon to search for {item} Sagar."

    def auto_update_system(self):
        try:
            # Runs winget upgrade --all in a new visible command prompt so the user can see progress
            subprocess.Popen('start cmd /k "echo SAAR is updating your apps... && winget upgrade --all"', shell=True)
            return "System update sequence initiated. Check the new terminal window Sagar."
        except Exception as e:
            return f"Failed to start system update: {e}"

# Global instance
web_assistant = WebAssistant()
