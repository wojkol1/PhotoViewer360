from qgis.PyQt import QtCore


class Slots(QtCore.QObject):
    """Simple class with one slot and one read-only property."""

    _x = 0.0
    _y = 0.0
    _id = -1
    _coordinates = []
    _index = ""
    signal = QtCore.pyqtSignal()


    def setXYId(self, coordinates):
        """definiuje wartości parametrów do przekazania do JS"""

        self._coordinates = coordinates

    @QtCore.pyqtSlot(str, str, str)
    def setXYtoPython(self, x, y, index):
        """definiuje wartości parametrów do przekazania do Python'a """

        self._x = x
        self._y = y
        self._index = index
        self.signal.emit()

    @QtCore.pyqtSlot(result=list)
    def getPhotoDetails(self):
        return [self._coordinates]

    @QtCore.pyqtSlot(result=list)
    def getHotSpotDetailsToPython(self):
        return [self._x, self._y, self._index]
