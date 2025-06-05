
import sys
import json
import socket
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel
)
from PyQt6.QtCore import QThread, pyqtSignal

class UDPListener(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, listen_ip, listen_port, response_enabled=True):
        super().__init__()
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.response_enabled = response_enabled
        self.running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.listen_ip, self.listen_port))
        sock.settimeout(1.0)
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                if message:
                    self.data_received.emit(f"📥 От {addr}: {message}")
                    if self.response_enabled and message.startswith("TX:"):
                        response = f"RX:{message[3:]}"
                        sock.sendto(response.encode('utf-8'), addr)
                        self.data_received.emit(f"📤 Ответ: {response}")
            except socket.timeout:
                continue
            except Exception as e:
                self.data_received.emit(f"Ошибка: {e}")
                break
        sock.close()

    def stop(self):
        self.running = False

class UDPEchoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.listener_thread = UDPListener("0.0.0.0", 5005)
        self.listener_thread.data_received.connect(self.append_message)

        self.setWindowTitle("UDP Echo Server")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Сервер слушает порт 5005. Ответы включены."))

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)

        self.setLayout(layout)
        self.listener_thread.start()

    def append_message(self, message):
        self.text_output.append(message)

    def closeEvent(self, event):
        self.listener_thread.stop()
        self.listener_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UDPEchoGUI()
    window.show()
    sys.exit(app.exec())
