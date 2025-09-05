# GUI.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QTextEdit
)
from PyQt5.QtGui import QMovie, QIcon
from PyQt5.QtCore import Qt, QSize, QEvent

# ------------------- Path Setup -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHICS_DIR = os.path.join(BASE_DIR, "Graphics")


# ------------------- GUI Class -------------------
class RiyaGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Riya Assistant")
        self.setGeometry(100, 100, 600, 500)
        self.setWindowIcon(QIcon(os.path.join(GRAPHICS_DIR, "Home.png")))

        # ------------------- Widgets -------------------
        # Riya GIF animation
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.movie = QMovie(os.path.join(GRAPHICS_DIR, "Jarvis.gif"))  # you can replace with Riya.gif
        self.label.setMovie(self.movie)
        self.movie.start()

        # Chat display
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)

        # Text input + send button
        self.input_box = QTextEdit(self)
        self.input_box.setFixedHeight(50)
        self.input_box.installEventFilter(self)  # enable Enter shortcut

        self.send_button = QPushButton("Send", self)

        # Mic button
        self.mic_button = QPushButton(self)
        self.mic_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Mic_off.png")))
        self.mic_button.setIconSize(QSize(48, 48))
        self.mic_button.clicked.connect(self.toggle_mic_icon)

        # Control buttons
        self.close_button = QPushButton(self)
        self.close_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Close.png")))
        self.close_button.setIconSize(QSize(32, 32))
        self.close_button.clicked.connect(self.close)

        self.min_button = QPushButton(self)
        self.min_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Minimize.png")))
        self.min_button.setIconSize(QSize(32, 32))
        self.min_button.clicked.connect(self.showMinimized)

        self.max_button = QPushButton(self)
        self.max_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Maximize.png")))
        self.max_button.setIconSize(QSize(32, 32))
        self.max_button.clicked.connect(self.showMaximized)

        # Extra options (home, chats, settings)
        self.home_button = QPushButton(self)
        self.home_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Home.png")))
        self.home_button.setIconSize(QSize(32, 32))

        self.chats_button = QPushButton(self)
        self.chats_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Chats.png")))
        self.chats_button.setIconSize(QSize(32, 32))

        self.settings_button = QPushButton(self)
        self.settings_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Settings.png")))
        self.settings_button.setIconSize(QSize(32, 32))

        # ------------------- Layout -------------------
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.chat_display)

        # Input + send
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Mic & extra options
        options_layout = QHBoxLayout()
        options_layout.addWidget(self.mic_button)
        options_layout.addStretch()
        options_layout.addWidget(self.home_button)
        options_layout.addWidget(self.chats_button)
        options_layout.addWidget(self.settings_button)
        layout.addLayout(options_layout)

        # Window control buttons
        window_controls = QHBoxLayout()
        window_controls.addStretch()
        window_controls.addWidget(self.min_button)
        window_controls.addWidget(self.max_button)
        window_controls.addWidget(self.close_button)
        layout.addLayout(window_controls)

        self.setLayout(layout)

        # State for mic button
        self.mic_on = False

    # ------------------- Functions -------------------
    def toggle_mic_icon(self):
        """Toggle mic button icon and show 'Listening...' when ON"""
        if self.mic_on:
            self.mic_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Mic_off.png")))
            self.mic_on = False
            self.chat_display.append("🔴 Riya: Goodbye")
        else:
            self.mic_button.setIcon(QIcon(os.path.join(GRAPHICS_DIR, "Mic_on.png")))
            self.mic_on = True
            self.chat_display.append("🟢 Riya: Listening...")

    # ------------------- Event Filter for Enter Key -------------------
    def eventFilter(self, source, event):
        if source is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() == Qt.ShiftModifier:
                    return False  # allow new line with Shift+Enter
                else:
                    self.send_button.click()  # simulate send
                    return True  # block newline
        return super().eventFilter(source, event)


# ------------------- Main -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    riya = RiyaGUI()
    riya.show()
    sys.exit(app.exec_())

