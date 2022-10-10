# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_orbitalDialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets
from .. import plugin_dir
from qgis.gui import QgsFileWidget

class Ui_orbitalDialog(object):
    def setupUi(self, orbitalDialog):
        orbitalDialog.setObjectName("orbitalDialog")
        orbitalDialog.resize(563, 375)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(orbitalDialog.sizePolicy().hasHeightForWidth())
        orbitalDialog.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(plugin_dir + "/images/icon.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        orbitalDialog.setWindowIcon(icon)
        orbitalDialog.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.ViewerLayout = QtWidgets.QGridLayout()
        self.ViewerLayout.setObjectName("ViewerLayout")
        self.verticalLayout_3.addLayout(self.ViewerLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.horizontalLayout.setObjectName("horizontalLayout")

        spacerItem = QtWidgets.QSpacerItem(
            5, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout.addItem(spacerItem)

        # self.label = QtWidgets.QLabel(self.dockWidgetContents)
        # self.label.setAlignment(QtCore.Qt.AlignCenter)
        # self.label.setObjectName("label")
        # self.horizontalLayout.addWidget(self.label)

        # self.QgsFileWidget_save_img = QgsFileWidget(self.dockWidgetContents)
        # self.QgsFileWidget_save_img.setUseLink(False)
        # self.QgsFileWidget_save_img.setFullUrl(False)
        # self.QgsFileWidget_save_img.setStorageMode(QgsFileWidget.SaveFile)
        # self.QgsFileWidget_save_img.setObjectName("QgsFileWidget_save_img")
        # self.horizontalLayout.addWidget(self.QgsFileWidget_save_img)

        self.btn_screenshot = QtWidgets.QPushButton(self.dockWidgetContents)
        self.btn_screenshot.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_screenshot.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(
            QtGui.QPixmap(plugin_dir + "/images/camera.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.btn_screenshot.setIcon(icon1)
        self.btn_screenshot.setObjectName("btn_screenshot")
        self.horizontalLayout.addWidget(self.btn_screenshot)

        # spacerItem1 = QtWidgets.QSpacerItem(
        #     5, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        # )
        # self.horizontalLayout.addItem(spacerItem1)

        self.btn_fullscreen = QtWidgets.QPushButton(self.dockWidgetContents)
        self.btn_fullscreen.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_fullscreen.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(
            QtGui.QPixmap(plugin_dir + "/images/full_screen.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.btn_fullscreen.setIcon(icon3)
        self.btn_fullscreen.setCheckable(True)
        self.btn_fullscreen.setObjectName("btn_fullscreen")
        self.horizontalLayout.addWidget(self.btn_fullscreen)

        spacerItem1 = QtWidgets.QSpacerItem(
            5, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        self.horizontalLayout.addItem(spacerItem1)

        self.verticalLayout_3.addLayout(self.horizontalLayout)
        orbitalDialog.setWidget(self.dockWidgetContents)

        self.retranslateUi(orbitalDialog)
        self.btn_fullscreen.clicked["bool"].connect(orbitalDialog.FullScreen)
        self.btn_screenshot.clicked.connect(orbitalDialog.GetScreenShot)
        QtCore.QMetaObject.connectSlotsByName(orbitalDialog)

    def retranslateUi(self, orbitalDialog):
        _translate = QtCore.QCoreApplication.translate
        orbitalDialog.setWindowTitle(
            _translate("orbitalDialog", "PhotoViewer360")
        )
        # self.label.setText(_translate("main", "Wybierz ściężkę zapisu zrzutu widoku: "))
