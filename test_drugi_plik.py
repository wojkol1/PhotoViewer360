from test import Test

class Test1():
    
    def __init__(self):
        self.test = Test()
        self.test.newPoint.connect(self.xxxx)

    def xxxx(self):
        print(" Connect")


test1 = Test1()
test1.test.emit_signal()