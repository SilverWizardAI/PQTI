"""
Simple PyQt6 test application for instrumentation PoC.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLineEdit, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt


class SimpleTestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PyQt Instrument Test App")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.text_input = QLineEdit()
        self.text_input.setObjectName("text_input")
        self.text_input.setPlaceholderText("Enter text here...")
        layout.addWidget(self.text_input)

        self.copy_button = QPushButton("Copy to Label")
        self.copy_button.setObjectName("copy_button")
        self.copy_button.clicked.connect(self.copy_text)
        layout.addWidget(self.copy_button)

        self.result_label = QLabel("Result will appear here")
        self.result_label.setObjectName("result_label")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        self.checkbox = QCheckBox("Enable feature")
        self.checkbox.setObjectName("feature_checkbox")
        self.checkbox.stateChanged.connect(self.checkbox_changed)
        layout.addWidget(self.checkbox)

        self.checkbox_label = QLabel("Feature: Disabled")
        self.checkbox_label.setObjectName("checkbox_status")
        layout.addWidget(self.checkbox_label)

        self.counter_button = QPushButton("Click me! (0)")
        self.counter_button.setObjectName("counter_button")
        self.counter_button.clicked.connect(self.increment_counter)
        layout.addWidget(self.counter_button)

        layout.addStretch()

    def copy_text(self):
        text = self.text_input.text()
        self.result_label.setText(f"You entered: {text}")

    def checkbox_changed(self, state):
        if state == Qt.CheckState.Checked.value:
            self.checkbox_label.setText("Feature: Enabled")
        else:
            self.checkbox_label.setText("Feature: Disabled")

    def increment_counter(self):
        self.counter += 1
        self.counter_button.setText(f"Click me! ({self.counter})")


def main():
    app = QApplication(sys.argv)

    try:
        from qt_instrument import enable_instrumentation
        enable_instrumentation(app)
        print("Instrumentation enabled - MCP server can now connect")
    except ImportError:
        print("qt_instrument not installed - running without instrumentation")

    window = SimpleTestApp()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
