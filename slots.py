from qgis.PyQt import QtCore, QtWidgets
import sys


class Slots(QtCore.QObject):
    """Simple class with one slot and one read-only property."""

    @QtCore.pyqtSlot(str)
    def showMessage(self, msg):
        """Open a message box and display the specified message."""
        QtWidgets.QMessageBox.information(None, "Info", msg)

