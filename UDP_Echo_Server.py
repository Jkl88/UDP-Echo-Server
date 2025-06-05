import sys
import socket
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal

class UDPListener(QThread):
    data_received = pyqtSignal(str, tuple)

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.running = True
        self.sock.settimeout(1.0)

    def run(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                if message:
                    self.data_received.emit(f"📥 Получено: {message}", addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.data_received.emit(f"Ошибка: {e}", ("", 0))
                break

    def stop(self):
        self.running = False

class UDPEchoGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.listen_ip = "0.0.0.0"
        self.listen_port = 5005
        self.send_port = 5005
        self.local_ip = socket.gethostbyname(socket.gethostname())

        self.setWindowTitle("UDP Echo Server")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        self.info_label = QLabel(f"Локальный IP: {self.local_ip}")
        layout.addWidget(self.info_label)

        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Порт приёма:"))
        self.port_input = QLineEdit(str(self.listen_port))
        port_layout.addWidget(self.port_input)

        port_layout.addWidget(QLabel("Отправки:"))
        self.send_port_input = QLineEdit(str(self.send_port))
        port_layout.addWidget(self.send_port_input)

        self.start_button = QPushButton("Запустить")
        self.start_button.clicked.connect(self.start_listener)
        port_layout.addWidget(self.start_button)
        layout.addLayout(port_layout)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)

        reply_layout = QHBoxLayout()
        self.reply_input = QLineEdit()
        self.reply_input.setPlaceholderText("Введите сообщение для отправки")
        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.send_reply)
        reply_layout.addWidget(self.reply_input)
        reply_layout.addWidget(self.send_button)
        layout.addLayout(reply_layout)

        self.setLayout(layout)

        self.listener_thread = None
        self.last_sender = None
        self.sock = None

    def start_listener(self):
        if self.listener_thread:
            self.listener_thread.stop()
            self.listener_thread.wait()
            self.listener_thread = None

        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        try:
            self.listen_port = int(self.port_input.text())
            self.send_port = int(self.send_port_input.text())

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.listen_ip, self.listen_port))
            self.listener_thread = UDPListener(self.sock)
            self.listener_thread.data_received.connect(self.handle_incoming)
            self.listener_thread.start()
            self.append_message(f"🔊 Слушаем на {self.listen_ip}:{self.listen_port}, отправка на порт {self.send_port}")
        except Exception as e:
            self.append_message(f"Ошибка запуска: {e}")

    def handle_incoming(self, message, addr):
        if addr != ("", 0):
            self.last_sender = addr
        self.append_message(message)

    def send_reply(self):
        if self.last_sender and self.sock:
            try:
                msg = self.reply_input.text().strip()
                if msg:
                    target_addr = (self.last_sender[0], self.send_port)
                    self.sock.sendto(msg.encode('utf-8'), target_addr)
                    self.append_message(f"📤 Отправлено: {msg}")
                    self.reply_input.clear()
            except Exception as e:
                self.append_message(f"Ошибка отправки: {e}")
        else:
            self.append_message("⚠️ Нет адреса для ответа")

    def append_message(self, message):
        self.text_output.append(message)

    def closeEvent(self, event):
        if self.listener_thread:
            self.listener_thread.stop()
            self.listener_thread.wait()
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UDPEchoGUI()
    window.show()
    sys.exit(app.exec())