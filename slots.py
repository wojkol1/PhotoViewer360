from unicodedata import name
from qgis.PyQt import QtCore, QtWidgets
import sys
from PyQt5.QtCore import QObject, pyqtSignal


# class _ChoseHotSpot(QObject):
#     newPoint = pyqtSignal()

#     def __init__(self):
#         QObject.__init__(self)
        
#     def emit_signal(self):
        
#         self.newPoint.emit()
#         print("_ChoseHotSpot")
    

class Slots(QtCore.QObject):
    """Simple class with one slot and one read-only property."""
    _x = 0.0
    _y = 0.0
    _index = ""
    _id = -1
    _coordinates = []
    _change = False
    newPoint = pyqtSignal()

    # def __init__(self):
    #     self.newPoint = pyqtSignal()

    # def emit_signal(self):
        
    #     self.newPoint.emit()
    #     print("_ChoseHotSpot")


    # def setXYId(self, x, y, id):
    #     """definiuje wartości parametrów do przekazania do JS"""
    #     self._x = x
    #     self._y = y
    #     self._id = id

    def setXYId(self, coordinates):
        """definiuje wartości parametrów do przekazania do JS"""
        self._coordinates = coordinates

    @QtCore.pyqtSlot(str)
    def showMessage(self, msg):
        """Open a message box and display the specified message."""
        QtWidgets.QMessageBox.information(None, "Info", msg)

    # @QtCore.pyqtSlot(result=list)
    # def getPhotoDetails(self):
    #     return [self._id, self._x, self._y]

    @QtCore.pyqtSlot(result=list)
    def getPhotoDetails(self):
        return [self._coordinates]

    @QtCore.pyqtSlot(str, str, str)
    def setXYtoPython(self, x, y, index):
        """definiuje wartości parametrów do przekazania do Python"""
        self._x = x
        self._y = y
        self._index = index
        print("wykryto hot spot slot !!!!!!!!!")
        self.emit_signal()

    # @QtCore.pyqtSignal()
    def emit_signal(self):
        print("Emit signal")
        self.newPoint.emit()

    # @QtCore.pyqtSlot(str)
    # def setXYtoPython(self, x, y, index, change):
    #     """definiuje wartości parametrów do przekazania do Python"""
    #     self._x = x
    #     self._y = y
    #     self._index = index
    #     self._change = change
    #     print("wykryto hot spot !!!!!!!!!")
    #     # hotSpot = _ChoseHotSpot()
    #     # hotSpot.connect_and_emit_trigger()

    @QtCore.pyqtSlot(result=list)
    def getHotSpotDetailsToPython(self):
        return [self._x, self._y, self._index]


# class Test1():
    
#     def __init__(self):
#         self.slot = Slots()
#         self.slot.newPoint.connect(self.xxxx)

#     def xxxx(self):
#         print(" Connect")

# test1 = Test1()
# test1.slot.newPoint.emit()

