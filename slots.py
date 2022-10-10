from qgis.PyQt import QtCore, QtWidgets
import sys


class Slots(QtCore.QObject):
    """Simple class with one slot and one read-only property."""
    _x = 0.0
    _y = 0.0
    _id = -1

    def setXYId(self, x, y, id):
        """definiuje wartości parametrów do przekazania do JS"""
        self._x = x
        self._y = y
        self._id = id

    @QtCore.pyqtSlot(str)
    def showMessage(self, msg):
        """Open a message box and display the specified message."""
        QtWidgets.QMessageBox.information(None, "Info", msg)

    @QtCore.pyqtSlot(result=list)
    def getPhotoDetails(self):
        return [self._id, self._x, self._y]
