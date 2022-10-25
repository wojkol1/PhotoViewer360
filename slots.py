from qgis.PyQt import QtCore, QtWidgets
import sys


class Slots(QtCore.QObject):
    """Simple class with one slot and one read-only property."""
    _x = 0.0
    _y = 0.0
    _id = -1
    _coordinates = []
    _index = ""
    signal = QtCore.pyqtSignal()
    # def setXYId(self, x, y, id):
    #     """definiuje wartości parametrów do przekazania do JS"""
    #     self._x = x
    #     self._y = y
    #     self._id = id

    def setXYId(self, coordinates):
        """definiuje wartości parametrów do przekazania do JS"""
        self._coordinates = coordinates

    # @QtCore.pyqtSlot(str)
    # def showMessage(self, msg):
    #     """Open a message box and display the specified message."""
    #     QtWidgets.QMessageBox.information(None, "Info", msg)
        # print('ttt')
        # self.signal.emit()
        
    # @QtCore.pyqtSlot(result=list)
    # def getPhotoDetails(self):
    #     return [self._id, self._x, self._y]

    @QtCore.pyqtSlot(str, str, str)
    def setXYtoPython(self, x, y, index):
        """definiuje wartości parametrów do przekazania do Python"""
        self._x = x
        self._y = y
        self._index = index
        print("wykryto hot spot slot !!!!!!!!!")
        print(x, " ", y, " ", index)
        self.signal.emit()

    @QtCore.pyqtSlot(result=list)
    def getPhotoDetails(self):
        return [self._coordinates]

    # def setXYtoPython(self, x, y, change):
    #     """definiuje wartości parametrów do przekazania do Python"""
    #     self._x = x
    #     self._y = y
    #     self._change = change

    @QtCore.pyqtSlot(result=list)
    def getHotSpotDetailsToPython(self):
        return [self._x, self._y, self._index]
