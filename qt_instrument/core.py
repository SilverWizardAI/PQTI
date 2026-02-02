"""
Core instrumentation functionality for PyQt6 applications.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class WidgetInspector:
    """Inspect and traverse PyQt6 widget trees."""

    @staticmethod
    def create_snapshot(root_widget: Optional[QWidget] = None) -> Dict[str, Any]:
        """Create a snapshot of the widget tree."""
        if root_widget is None:
            # Get all top-level windows
            windows = QApplication.topLevelWidgets()
            if not windows:
                return {"error": "No windows found"}
            root_widget = windows[0]

        return WidgetInspector._traverse_widget(root_widget, "root")

    @staticmethod
    def _traverse_widget(widget: QWidget, path: str) -> Dict[str, Any]:
        """Recursively traverse widget tree."""
        snapshot = {
            "ref": path,
            "type": widget.__class__.__name__,
            "objectName": widget.objectName() or None,
            "visible": widget.isVisible(),
            "enabled": widget.isEnabled(),
            "geometry": {
                "x": widget.x(),
                "y": widget.y(),
                "width": widget.width(),
                "height": widget.height(),
            },
            "properties": WidgetInspector._extract_properties(widget),
            "children": [],
        }

        # Traverse child widgets
        children = [child for child in widget.children() if isinstance(child, QWidget)]
        for i, child in enumerate(children):
            child_ref = f"{path}/{child.__class__.__name__}[{i}]"
            if child.objectName():
                child_ref = f"{path}/{child.objectName()}"
            snapshot["children"].append(
                WidgetInspector._traverse_widget(child, child_ref)
            )

        return snapshot

    @staticmethod
    def _extract_properties(widget: QWidget) -> Dict[str, Any]:
        """Extract widget-specific properties."""
        props = {}

        # Common properties
        if hasattr(widget, "text") and callable(widget.text):
            props["text"] = widget.text()
        if hasattr(widget, "isChecked") and callable(widget.isChecked):
            props["checked"] = widget.isChecked()
        if hasattr(widget, "value") and callable(widget.value):
            props["value"] = widget.value()
        if hasattr(widget, "currentText") and callable(widget.currentText):
            props["currentText"] = widget.currentText()
        if hasattr(widget, "placeholderText") and callable(widget.placeholderText):
            props["placeholder"] = widget.placeholderText()

        return props

    @staticmethod
    def find_widget_by_ref(ref: str) -> Optional[QWidget]:
        """Find widget by reference path."""
        parts = ref.split("/")
        if not parts or parts[0] != "root":
            return None

        # Start with first top-level widget
        windows = QApplication.topLevelWidgets()
        if not windows:
            return None
        widget = windows[0]

        # Traverse path
        for part in parts[1:]:
            if not part:
                continue

            # Check if it's an objectName reference
            child = widget.findChild(QWidget, part)
            if child:
                widget = child
                continue

            # Check if it's an indexed reference like "QPushButton[0]"
            if "[" in part:
                class_name = part.split("[")[0]
                index = int(part.split("[")[1].rstrip("]"))
                children = [
                    c
                    for c in widget.children()
                    if isinstance(c, QWidget) and c.__class__.__name__ == class_name
                ]
                if index < len(children):
                    widget = children[index]
                else:
                    return None
            else:
                return None

        return widget


class WidgetActions:
    """Perform actions on PyQt6 widgets."""

    @staticmethod
    def click(widget: QWidget, button: str = "left") -> Dict[str, Any]:
        """Click a widget."""
        if not widget.isVisible():
            return {"success": False, "error": "Widget not visible"}
        if not widget.isEnabled():
            return {"success": False, "error": "Widget not enabled"}

        button_map = {
            "left": Qt.MouseButton.LeftButton,
            "right": Qt.MouseButton.RightButton,
            "middle": Qt.MouseButton.MiddleButton,
        }

        qt_button = button_map.get(button, Qt.MouseButton.LeftButton)
        QTest.mouseClick(widget, qt_button)

        return {"success": True}

    @staticmethod
    def type_text(widget: QWidget, text: str, submit: bool = False) -> Dict[str, Any]:
        """Type text into a widget."""
        if not widget.isVisible():
            return {"success": False, "error": "Widget not visible"}
        if not widget.isEnabled():
            return {"success": False, "error": "Widget not enabled"}

        widget.setFocus()
        QTest.keyClicks(widget, text)

        if submit:
            QTest.keyClick(widget, Qt.Key.Key_Return)

        return {"success": True}


class InstrumentationServer(QObject):
    """IPC server for receiving instrumentation commands."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = QLocalServer(self)
        self.connections: List[QLocalSocket] = []
        self.server.newConnection.connect(self._handle_new_connection)

    def start(self, server_name: str = "qt_instrument") -> bool:
        """Start the IPC server."""
        # Remove any existing server
        QLocalServer.removeServer(server_name)

        if not self.server.listen(server_name):
            logger.error(f"Failed to start server: {self.server.errorString()}")
            return False

        logger.info(f"Instrumentation server listening on: {server_name}")
        return True

    def _handle_new_connection(self):
        """Handle new client connection."""
        socket = self.server.nextPendingConnection()
        if socket:
            self.connections.append(socket)
            socket.readyRead.connect(lambda: self._handle_message(socket))
            socket.disconnected.connect(lambda: self._handle_disconnect(socket))
            logger.info("Client connected")

    def _handle_disconnect(self, socket: QLocalSocket):
        """Handle client disconnect."""
        if socket in self.connections:
            self.connections.remove(socket)
        socket.deleteLater()
        logger.info("Client disconnected")

    def _handle_message(self, socket: QLocalSocket):
        """Handle incoming message from client."""
        try:
            data = bytes(socket.readAll()).decode("utf-8")
            request = json.loads(data)
            logger.info(f"Received request: {request}")

            response = self._process_request(request)

            # Send response
            socket.write(json.dumps(response).encode("utf-8"))
            socket.flush()

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            error_response = {
                "id": request.get("id") if "request" in locals() else None,
                "error": str(e),
            }
            socket.write(json.dumps(error_response).encode("utf-8"))
            socket.flush()

    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return response."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        result = {}

        if method == "snapshot":
            result = WidgetInspector.create_snapshot()

        elif method == "click":
            ref = params.get("ref")
            button = params.get("button", "left")
            widget = WidgetInspector.find_widget_by_ref(ref)

            if widget:
                result = WidgetActions.click(widget, button)
            else:
                result = {"success": False, "error": f"Widget not found: {ref}"}

        elif method == "type":
            ref = params.get("ref")
            text = params.get("text", "")
            submit = params.get("submit", False)
            widget = WidgetInspector.find_widget_by_ref(ref)

            if widget:
                result = WidgetActions.type_text(widget, text, submit)
            else:
                result = {"success": False, "error": f"Widget not found: {ref}"}

        elif method == "ping":
            result = {"status": "ok"}

        else:
            result = {"error": f"Unknown method: {method}"}

        return {"id": request_id, "result": result}


# Global server instance
_server: Optional[InstrumentationServer] = None


def enable_instrumentation(app: QApplication, server_name: str = "qt_instrument") -> bool:
    """
    Enable instrumentation for a PyQt6 application.

    Args:
        app: The QApplication instance
        server_name: Name for the IPC server (default: qt_instrument)

    Returns:
        True if instrumentation was successfully enabled
    """
    global _server

    if _server is not None:
        logger.warning("Instrumentation already enabled")
        return True

    logging.basicConfig(level=logging.INFO)

    _server = InstrumentationServer(app)
    success = _server.start(server_name)

    if success:
        logger.info("Instrumentation enabled successfully")
    else:
        logger.error("Failed to enable instrumentation")
        _server = None

    return success
