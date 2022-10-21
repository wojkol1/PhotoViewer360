from PyQt5.QtCore import QObject, pyqtSignal

class Test(QObject):
    newPoint = pyqtSignal()

    def emit_signal(self):
        self.newPoint.emit()

