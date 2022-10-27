"""
/***************************************************************************
 PhotoViewer360
                                 A QGIS plugin
 Show local equirectangular images.
                             -------------------
        begin                : 2017-02-17
        copyright            : (C) 2016 All4Gis.
        email                : franka1986@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 #   any later version.                                                    *
 *                                                                         *
 ***************************************************************************/
"""

from gzip import FTEXT
import math
import sys
import processing
import os
import json
from os.path import basename
from qgis.core import (
    QgsPointXY,
    QgsProject,
    QgsFeatureRequest,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsGeometry,
    QgsProcessingFeatureSourceDefinition,
    QgsCoordinateReferenceSystem
)
from qgis.gui import QgsRubberBand

from qgis.PyQt.QtCore import (
    QObject,
    QUrl,
    Qt,
    pyqtSignal,
    QSize,
    QSettings,
    QRect,
    QPoint,
    QBuffer
)
from qgis.PyQt.QtWidgets import QDialog, QWidget, QDockWidget, QPushButton, QFileDialog, QApplication
from qgis.PyQt.QtGui import QWindow, QColor, QImage, QPainter, QScreen
import PhotoViewer360.config as config
from PhotoViewer360.geom.transformgeom import transformGeometry
from PhotoViewer360.gui.ui_orbitalDialog import Ui_orbitalDialog
from PhotoViewer360.utils.qgsutils import qgsutils
from qgis.PyQt.QtWebKitWidgets import QWebView, QWebPage
from qgis.PyQt.QtWebKit import QWebSettings
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QDate, QDateTime

from .slots import Slots

try:
    from pydevd import *
except ImportError:
    None

try:
    from PIL import Image
except ImportError:
    None


class _ViewerPage(QWebPage):
    obj = []  # synchronous
    newData = pyqtSignal(list)  # asynchronous

    def javaScriptConsoleMessage(self, msg, line, source):
        l = msg.split(",")
        # print(msg)
        if 'yaw' in l[0]:
            # print(l[0])
            # print(l)
            self.obj = l
            self.newData.emit(l)

class Geo360Dialog(QDockWidget, Ui_orbitalDialog):
    """Geo360 Dialog Class"""

    def __init__(self, iface, parent=None, featuresId=None, layer=None, name_layer=""):

        QDockWidget.__init__(self)

        self.useLayer = name_layer

        self.setupUi(self)

        self.DEFAULT_URL = (
                "http://" + config.IP + ":" + str(config.PORT) + "/viewer.html"
        )
        self.DEFAULT_EMPTY = (
                "http://" + config.IP + ":" + str(config.PORT) + "/none.html"
        )
        self.DEFAULT_BLANK = (
                "http://" + config.IP + ":" + str(config.PORT) + "/blank.html"
        )

        # Create Viewer
        self.CreateViewer()

        self.plugin_path = os.path.dirname(os.path.realpath(__file__))
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.parent = parent

        # Orientation from image
        self.yaw = math.pi
        self.bearing = None

        self.layer = layer
        self.featuresId = featuresId

        self.actualPointDx = None
        self.actualPointSx = None
        self.actualPointOrientation = None

        self.actualPointOrientation = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.LineGeometry
        )
        self.positionDx = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )
        self.positionInt = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )
        self.positionSx = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )

        self.selected_features = qgsutils.getToFeature(self.layer, self.featuresId)


        # Get image path
        self.current_image = self.GetImage()
        print("type path image: ", self.current_image)

        # Check if image exist
        if os.path.exists(self.current_image) is False:
            qgsutils.showUserAndLogMessage(
                u"Information: ", u"There is no associated image."
            )
            self.resetQgsRubberBand()
            self.ChangeUrlViewer(self.DEFAULT_EMPTY)
            return

        # Copy file to local server
        self.CopyFile(self.current_image)

        # Set RubberBand
        self.resetQgsRubberBand()
        self.UpdateOrientation()
        self.setPosition()

        # FullScreen
        self.isWindowFullScreen = False
        self.normalWindowState = None

        # Hotspot
        self.slots.signal.connect(self.ClickHotspot)
        
        # self.old_bearing = None
        

    def __del__(self):
        self.resetQgsRubberBand()

    def onNewData(self, data):
        try:
            print(data[0].replace("yaw=",""))
            newYaw = float(data[0].replace("yaw=",""))
            self.UpdateOrientation(yaw=newYaw)
        except:
            None

    def CreateViewer(self):
        """Create Viewer"""

        qgsutils.showUserAndLogMessage(u"Information: ", u"Create viewer", onlyLog=True)

        self.cef_widget = QWebView()
        self.cef_widget.setContextMenuPolicy(Qt.NoContextMenu)

        self.cef_widget.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        pano_view_settings = self.cef_widget.settings()
        pano_view_settings.setAttribute(QWebSettings.WebGLEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.Accelerated2dCanvasEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.JavascriptEnabled, True)

        self.page = _ViewerPage()
        self.page.newData.connect(self.onNewData)
        self.cef_widget.setPage(self.page)

        """ połaczenie z javascriptem"""
        self.slots = Slots()

        # self.slots.setXYId(x=123, y=456, id=987)    # push params to JS
        self.cef_widget.page().mainFrame().addToJavaScriptWindowObject("pythonSlot", self.slots)

        self.cef_widget.load(QUrl(self.DEFAULT_URL))
        self.ViewerLayout.addWidget(self.cef_widget, 1, 0)

    # def SetInitialYaw(self):
    #     """Set Initial Viewer Yaw"""
    #     self.bearing = self.selected_features.attribute(config.column_yaw)
    #     # self.view.browser.GetMainFrame().ExecuteFunction("InitialYaw",
    #     #                                                  self.bearing)
    #     return

    def RemoveImage(self):
        """Remove Image"""
        try:
            os.remove(self.plugin_path + "/viewer/image.jpg")
        except OSError:
            pass

    def CopyFile(self, src):
        """Copy Image File in Local Server"""
        qgsutils.showUserAndLogMessage(u"Information: ", u"Copying image", onlyLog=True)

        src_dir = src
        dst_dir = self.plugin_path + "/viewer"

        # Copy image in local folder
        img = Image.open(src_dir)
        rgb_im = img.convert("RGB")
        a = self.current_image
        name_img = basename(a)
        dst_dir = dst_dir + "/" + "image.jpg"

        try:
            os.remove(dst_dir)
        except OSError:
            pass

        rgb_im.save(dst_dir)

        # Utworzenie pliku html z danymi pozyskanymi z nazwy zdjęcia
        file_metadata = open(self.plugin_path + '/viewer/file_metadata.html', 'w')

        # get dataTime
        dateTime = "Brak daty"
        for feature in self.layer.getFeatures():
            if feature.attributes()[2] == name_img.split(".")[0]:
                dateTime = feature.attributes()[7]
                dateTime = str(dateTime.toString(Qt.ISODate)).replace("T", " ")
                nr_drogi = str(feature.attributes()[8])
                nazwa_ulicy = str(feature.attributes()[9])
                numer_odcinka = str(feature.attributes()[10])
                kilometraz = str(feature.attributes()[11])

        if nazwa_ulicy == "NULL":
            print(" nazwa ulicy null")
            file_metadata.write(
                '<!DOCTYPE html>' + '\n' + '<html lang="pl">' + '\n' + '<head>' + '\n' + '   <meta charset="UTF-8">' + '\n' + '  <title>Photos metadata</title>' + '\n' + '</head>' + '\n' + '<body>' + '\n' + ' <div id="photo_data" style="position: absolute; top: 0; left: 0px; padding-top: 0px;width: 250px; max-height: 100%; overflow: hidden; margin-left: 0; background-color: rgba(58,68,84,0.8); color:white; font-family: inherit; line-height: 0.7;">' + '\n')
            file_metadata.write('<p style="margin-left: 5px;">' + "<b>" + "Numer drogi: " + "</b>" + "</p>")
            file_metadata.write('<p style="margin-left: 5px;">' + nr_drogi + "</p>")
        else:
            file_metadata.write(
                '<!DOCTYPE html>' + '\n' + '<html lang="pl">' + '\n' + '<head>' + '\n' + '   <meta charset="UTF-8">' + '\n' + '  <title>Photos metadata</title>' + '\n' + '</head>' + '\n' + '<body>' + '\n' + ' <div id="photo_data" style="position: absolute; top: 0; left: 0px; padding-top: 0px;width: 220px; max-height: 100%; overflow: hidden; margin-left: 0; background-color: rgba(58,68,84,0.8); color:white; font-family: inherit; line-height: 0.7;">' + '\n')
            file_metadata.write('<p style="margin-left: 5px;">' + "<b>" + "Numer drogi: " + "</b>" + nr_drogi + "</p>")
            file_metadata.write(
                '<p style="margin-left: 5px;">' + "<b>" + "Nazwa ulicy: " + "</b>" + nazwa_ulicy + "</p>")
            file_metadata.write(
                '<p style="margin-left: 5px;">' + "<b>" + "Numer odcinka: " + "</b>" + numer_odcinka + "</p>")
            file_metadata.write('<p style="margin-left: 5px;">' + "<b>" + "Kilometraż: " + "</b>" + kilometraz + "</p>")

        file_metadata.write('<p style="margin-left: 5px;">' + "<b>" + "Data: " + "</b>" + dateTime + "</p>")
        file_metadata.write("</div>" + "\n" + "    </div>" + "\n" + "</body>" + "\n" + "</html>")
        file_metadata.close()

    def GetImage(self):

        """Create buffer"""
        self.layer.select(self.selected_features.id())

        features = self.layer.selectedFeatures()
        for feat in features:
            x_punktu = feat.attributes()[5] # z geometrii fead.geometry(aspoint
            y_punktu = feat.attributes()[6]

        selected_feature_2180 = processing.run("native:reprojectlayer", {
            'INPUT': QgsProcessingFeatureSourceDefinition(self.layer.name(), selectedFeaturesOnly=True, featureLimit=-1,
                                                          geometryCheck=QgsFeatureRequest.GeometryAbortOnInvalid),
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:2180'),
            'OPERATION': '+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=tmerc +lat_0=0 +lon_0=19 +k=0.9993 +x_0=500000 +y_0=-5300000 +ellps=GRS80',
            'OUTPUT': 'TEMPORARY_OUTPUT'})

        bufor_2180 = processing.run("native:buffer", {
            'INPUT': list(selected_feature_2180.values())[0],
            'DISTANCE': 10, 'SEGMENTS': 5, 'END_CAP_STYLE': 0, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'DISSOLVE': False,
            'OUTPUT': 'TEMPORARY_OUTPUT'})

        # QgsProject.instance().addMapLayer(list(bufor_2180.values())[0])

        point_selected = processing.run("native:selectbylocation",
                                        {'INPUT': self.layer.name(), 'PREDICATE': 0,
                                         'INTERSECT': list(bufor_2180.values())[0], 'METHOD': 0})

        """Get Coordinates of an Image and Hotspots"""
        # współrzędne w układzie EPSG:4326
        list_of_attribute_list = []
        for feat in self.layer.selectedFeatures():
            x = feat.attributes()[5]
            y = feat.attributes()[6]
            azymut = feat.attributes()[4]
            index_feature = feat.id()
            print("index: ", index_feature)
            azymut_metadane = str(azymut).replace(",",".")
            print("azymut_metadane: ", azymut_metadane)


            centr = QgsPointXY(float(x), float(y))
            pkt = QgsPointXY(float(x_punktu), float(y_punktu))
            azymut_obliczony = centr.azimuth(pkt)
            print('azymut_obliczony: ', azymut_obliczony)
            
            # list_of_attribute_list.append(x + ' ' + y + ' ' + str((180 * azymut) / 200) + ' ' + str(index_feature))
            # try:
            #     list_of_attribute_list.append(x + ' ' + y + ' ' + str(self.old_bearing) + ' ' + str(index_feature) + ' ' + str(azymut_obliczony))
            # except AttributeError:
            list_of_attribute_list.append(x + ' ' + y + ' ' + azymut_metadane + ' ' + str(index_feature) + ' ' + str(azymut_obliczony))

            self.layer.removeSelection()

        self.slots.setXYId(coordinates=list_of_attribute_list)
        # coordinate_hotspot = self.slots.getHotSpotDetailsToPython()
        # print("coordinate_hotspot: ", coordinate_hotspot)

        """Get Selected Image"""
        try:
            path = qgsutils.getAttributeFromFeature(
                self.selected_features, config.column_name
            )
            if not os.path.isabs(path):  # Relative Path to Project
                path_project = QgsProject.instance().readPath("./")
                path = os.path.normpath(os.path.join(path_project, path))
                print(path)
        except Exception:
            qgsutils.showUserAndLogMessage(u"Information: ", u"Column not found.")
            return

        qgsutils.showUserAndLogMessage(u"Information: ", str(path), onlyLog=True)
        return path

    def ChangeUrlViewer(self, new_url):
        """Change Url Viewer"""
        self.cef_widget.load(QUrl(new_url))

    def ClickHotspot(self):
        """Reaload Image viewer after click hotspot"""

        print("click hotspot")
        coordinate_hotspot = self.slots.getHotSpotDetailsToPython()
        print("coordinate_hotspot: ", coordinate_hotspot)
        print('obsługa Sygnału')
        print("layer: ", self.layer)
        newId = int(coordinate_hotspot[2])

        self.ReloadView(newId)


    def ReloadView(self, newId):
        """Reaload Image viewer"""
        # self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        # # this will activate the window
        # self.activateWindow()

        self.cef_widget = QWebView()
        self.cef_widget.setContextMenuPolicy(Qt.NoContextMenu)

        self.cef_widget.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        pano_view_settings = self.cef_widget.settings()
        pano_view_settings.setAttribute(QWebSettings.WebGLEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.Accelerated2dCanvasEnabled, True)
        pano_view_settings.setAttribute(QWebSettings.JavascriptEnabled, True)

        self.page = _ViewerPage()
        self.page.newData.connect(self.onNewData)
        self.cef_widget.setPage(self.page)

        # """ połaczenie z javascriptem"""
        self.slots = Slots()

        # # self.slots.setXYId(x=123, y=456, id=987)    # push params to JS
        self.cef_widget.page().mainFrame().addToJavaScriptWindowObject("pythonSlot", self.slots)

        self.cef_widget.load(QUrl(self.DEFAULT_URL))
        self.ViewerLayout.addWidget(self.cef_widget, 1, 0)


        self.selected_features = qgsutils.getToFeature(self.layer, newId)
        print("ReloadView")

        # loc = self.plugin_path + "/viewer"
        # test = os.listdir(loc)
        # print(test)

        # for item in test:
        #     if (item.endswith(".jpg") or item.endswith(".png")) and not item.endswith("image.jpg") and not item.endswith("noImage.jpg"):
        #         os.remove(os.path.join(loc, item))

        self.current_image = self.GetImage()

        # Check if image exist
        if os.path.exists(self.current_image) is False:
            qgsutils.showUserAndLogMessage(
                u"Information: ", u"There is no associated image."
            )
            self.ChangeUrlViewer(self.DEFAULT_EMPTY)
            self.resetQgsRubberBand()
            return

        # Set RubberBand
        self.resetQgsRubberBand()
        self.UpdateOrientation()
        self.setPosition()

        # Copy file to local server
        self.CopyFile(self.current_image)

        self.ChangeUrlViewer(self.DEFAULT_URL)

        self.slots.signal.connect(self.ClickHotspot)

    def FullScreen(self):
        if not self.isWindowFullScreen:
            self.setFloating(True)
            self.normalWindowState = self.windowState()
            self.setWindowState(Qt.WindowFullScreen)
            self.cef_widget.showFullScreen()
            self.isWindowFullScreen = True
        else:
            self.cef_widget.showNormal()
            self.setWindowState(self.normalWindowState)
            self.setFloating(False)
            self.isWindowFullScreen = False

    def GetScreenShot(self):
        print("Screen Shot")

        image_path, extencion = QFileDialog.getSaveFileName(self.cef_widget, "Wskaż lokalizacje zrzutu ekranu",
                                                            "",
                                                            "PNG(*.png);;JPEG(*.jpg)")

        # gdy użytkownik nie wskaże pliku -> nic nie rób
        if not image_path:
            return

        pixmap = self.cef_widget.grab()
        pixmap.save(image_path)
        print("image path after save: ", image_path)
        print("self.bearing: ", self.bearing)

    def UpdateOrientation(self, yaw=None):
        """Update Orientation"""
        self.bearing = self.selected_features.attribute(config.column_yaw)

        originalPoint = self.selected_features.geometry().asPoint()
        self.actualPointDx = qgsutils.convertProjection(
            originalPoint.x(),
            originalPoint.y(),
            self.layer.crs().authid(),
            self.canvas.mapSettings().destinationCrs().authid(),
        ) 
        
        print("self.bearing: ", self.bearing)
        try:
            self.actualPointOrientation.reset()
            print("actualPointOrientation update orientation reset")
        except Exception:
            print("actualPointOrientation update orientation")
            pass

        self.actualPointOrientation = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.LineGeometry
        )
        self.actualPointOrientation.setColor(Qt.gray)
        self.actualPointOrientation.setWidth(5)

        # self.actualPointOrientation.addPoint(self.actualPointDx)

        # Lewy punkt
        CS = self.canvas.mapUnitsPerPixel() * 18
        A2x = self.actualPointDx.x() - CS
        A2y = self.actualPointDx.y() + CS
        self.actualPointOrientation.addPoint(QgsPointXY(float(A2x), float(A2y)))

        # Górny punkt strzałki
        CS = self.canvas.mapUnitsPerPixel() * 22
        A1x = self.actualPointDx.x()
        A1y = self.actualPointDx.y()
        self.actualPointOrientation.addPoint(QgsPointXY(float(A1x), float(A1y)))

        # Prawy punkt
        CS = self.canvas.mapUnitsPerPixel() * 18
        A3x = self.actualPointDx.x() + CS
        A3y = self.actualPointDx.y() + CS
        self.actualPointOrientation.addPoint(QgsPointXY(float(A3x), float(A3y)))

        # Następne punkty łuku strzałki
        CS = self.canvas.mapUnitsPerPixel() * 18
        A4x = self.actualPointDx.x() + CS * 0.75
        A4y = self.actualPointDx.y() + CS * 1.25
        self.actualPointOrientation.addPoint(QgsPointXY(float(A4x), float(A4y)))

        CS = self.canvas.mapUnitsPerPixel() * 18
        A44x = self.actualPointDx.x() + CS * 0.50
        A44y = self.actualPointDx.y() + CS * 1.45
        self.actualPointOrientation.addPoint(QgsPointXY(float(A44x), float(A44y)))

        CS = self.canvas.mapUnitsPerPixel() * 18
        A444x = self.actualPointDx.x() + CS * 0.25
        A444y = self.actualPointDx.y() + CS * 1.55
        self.actualPointOrientation.addPoint(QgsPointXY(float(A444x), float(A444y)))

        # Górny punkt łuku strzałki
        CS = self.canvas.mapUnitsPerPixel() * 18
        A5x = self.actualPointDx.x()
        A5y = self.actualPointDx.y() + CS * 1.6
        self.actualPointOrientation.addPoint(QgsPointXY(float(A5x), float(A5y)))

        # Następne punkty łuku strzałki
        CS = self.canvas.mapUnitsPerPixel() * 18
        A6x = self.actualPointDx.x() - CS * 0.25
        A6y = self.actualPointDx.y() + CS * 1.55
        self.actualPointOrientation.addPoint(QgsPointXY(float(A6x), float(A6y)))

        CS = self.canvas.mapUnitsPerPixel() * 18
        A66x = self.actualPointDx.x() - CS * 0.50
        A66y = self.actualPointDx.y() + CS * 1.45
        self.actualPointOrientation.addPoint(QgsPointXY(float(A66x), float(A66y)))

        CS = self.canvas.mapUnitsPerPixel() * 18
        A666x = self.actualPointDx.x() - CS * 0.75
        A666y = self.actualPointDx.y() + CS * 1.25
        self.actualPointOrientation.addPoint(QgsPointXY(float(A666x), float(A666y)))

        # # punkt kończący strzałkę
        CS = self.canvas.mapUnitsPerPixel() * 18
        Ax = self.actualPointDx.x() - CS
        Ay = self.actualPointDx.y() + CS
        self.actualPointOrientation.addPoint(QgsPointXY(float(Ax), float(Ay)))

        # Vision Angle
        if yaw is not None:
            # if self.old_bearing is not None:
            #     angle = float(self.old_bearing  + yaw) * math.pi / -180
            # else:
            #     angle = float(self.bearing  + yaw) * math.pi / -180

            # self.old_bearing = self.bearing + yaw
            # print("angle: ", angle)

            angle = float(self.bearing  + yaw) * math.pi / -180
        else:
            angle = float(self.bearing) * math.pi / -180


        tmpGeom = self.actualPointOrientation.asGeometry()

        self.rotateTool = transformGeometry()
        epsg = self.canvas.mapSettings().destinationCrs().authid()
        self.dumLayer = QgsVectorLayer(
            "Point?crs=" + epsg, "temporary_points", "memory"
        )
        self.actualPointOrientation.setToGeometry(
            self.rotateTool.rotate(tmpGeom, self.actualPointDx, angle), self.dumLayer
        )


    def setPosition(self):
        """Set RubberBand Position"""
        # Transform Point
        originalPoint = self.selected_features.geometry().asPoint()
        self.actualPointDx = qgsutils.convertProjection(
            originalPoint.x(),
            originalPoint.y(),
            "EPSG:4326",
            self.canvas.mapSettings().destinationCrs().authid(),
        )

        # try:
        #     self.positionDx.reset()
        #     print("positionDx reset")
        # except Exception:
        #     print("positionDx")
        #     pass

        self.positionDx = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )

        self.positionDx.setWidth(6)
        self.positionDx.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.positionDx.setIconSize(6)
        self.positionDx.setColor(QColor(0, 102, 153))

        # try:
        #     self.positionSx.reset()
        #     print("positionSx reset")
        # except Exception:
        #     print("positionSx")
        #     pass

        self.positionSx = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )

        self.positionSx.setWidth(5)
        self.positionSx.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.positionSx.setIconSize(4)
        self.positionSx.setColor(QColor(0, 102, 153))

        # try:
        #     self.positionInt.reset()
        #     print("positionInt reset")
        # except Exception:
        #     print("positionInt")
        #     pass

        self.positionInt = QgsRubberBand(
            self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        )

        self.positionInt.setWidth(5)
        self.positionInt.setIcon(QgsRubberBand.ICON_CIRCLE)
        self.positionInt.setIconSize(3)
        self.positionInt.setColor(Qt.white)

        self.positionDx.addPoint(self.actualPointDx)
        self.positionSx.addPoint(self.actualPointDx)
        self.positionInt.addPoint(self.actualPointDx)

    def closeEvent(self, _):
        """Close dialog"""
        self.resetQgsRubberBand()
        self.canvas.refresh()
        self.iface.actionPan().trigger()
        self.parent.orbitalViewer = None
        self.RemoveImage()

    def resetQgsRubberBand(self):
        """Remove RubbeBand"""
        print("reset qgis rubber band")
        try:
            self.positionSx.reset()
            self.positionInt.reset()
            self.positionDx.reset()
            self.actualPointOrientation.reset()
        except Exception:
            print("exception remove rubbeband")
            None
