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
import shutil

from qgis.gui import QgsMapToolIdentify
from qgis.PyQt.QtCore import Qt, QSettings, QThread, QVariant
from qgis.PyQt.QtGui import QIcon, QCursor, QPixmap
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QProgressBar

from . import plugin_dir
from PhotoViewer360.Geo360Dialog import Geo360Dialog
# from PhotoViewer360.gui.first_window_geo360_base import Ui_main
from PhotoViewer360.gui.first_window_geo360_dialog import FirstWindowGeo360Dialog
import PhotoViewer360.config as config
from PhotoViewer360.utils.log import log
from PhotoViewer360.utils.qgsutils import qgsutils
from qgis.core import QgsApplication
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time, os
import processing
from PyQt5.QtWidgets import QFileDialog
# from qgis.core import QgsVectorLayer
from qgis.core import *
from qgis.PyQt.QtWidgets import QDialog
from PyQt5 import QtWidgets
import sys
from qgis.gui import QgsFileWidget
from qgis.core import (
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand

# from PyQt4.QtCore import QVariant
from PIL import Image, ExifTags
import exifread
from .slots import Slots

try:
    from pydevd import *
except ImportError:
    None

""" Server Handelr """


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class Geo360:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):

        self.config = None
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        threadcount = QThread.idealThreadCount()
        # use all available cores and parallel rendering
        QgsApplication.setMaxThreads(threadcount)
        QSettings().setValue("/qgis/parallel_rendering", True)
        # OpenCL acceleration
        QSettings().setValue("/core/OpenClEnabled", True)
        self.orbitalViewer = None
        self.server = None
        self.actions = []
        self.make_server()
        self.dlg = FirstWindowGeo360Dialog()
        self.settings = QgsSettings()
        self.useLayer = ""
        self.is_press_button = False

        # self.actualPointOrientation = QgsRubberBand(
        #     self.iface.mapCanvas(), QgsWkbTypes.LineGeometry
        # )
        # self.positionDx = QgsRubberBand(
        #     self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        # )
        # self.positionInt = QgsRubberBand(
        #     self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        # )
        # self.positionSx = QgsRubberBand(
        #     self.iface.mapCanvas(), QgsWkbTypes.PointGeometry
        # )
        self.slots = Slots()

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        # if add_to_toolbar:
        #     # Adds plugin icon to Plugins toolbar
        #     # self.iface.addToolBarIcon(action)
        #     self.toolbar.addAction(action)
        #
        # if add_to_menu:
        #     self.iface.addPluginToMenu(
        #         self.menu,
        #         action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Add Geo360 tool"""
        log.initLogging()

        self.action = self.add_action(
            icon_path=QIcon(plugin_dir + "/images/icon.png"),
            text=u"PhotoViewer360",
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&PhotoViewer360", self.action)

        # # informacje o wersji
        # self.dlg.setWindowTitle('%s %s' % (plugin_name, plugin_version))
        # self.dlg.lbl_pluginVersion.setText('%s %s' % (plugin_name, plugin_version))

        # eventy
        self.dlg.fromLayer_btn.clicked.connect(self.fromLayer_btn_clicked)
        self.dlg.fromPhotos_btn.clicked.connect(self.fromPhotos_btn_clicked)
        self.dlg.fromGPKG_btn.clicked.connect(self.fromGPKG_btn_clicked)

        self.dlg.mQgsFileWidget_search_photo.setFilePath(
            self.settings.value("", ""))
        self.dlg.mQgsFileWidget_search_photo.fileChanged.connect(
            lambda: self.settings.setValue("",
                                           self.dlg.mQgsFileWidget_search_photo.filePath()))
        self.dlg.mQgsFileWidget_save_gpkg.setFilter("geoPackage(*.gpkg)")
        self.dlg.mQgsFileWidget_save_gpkg.setFilePath(
            self.settings.value(QgsProject.instance().homePath(),
                                QgsProject.instance().homePath() + "/plik_geopackage"))
        self.dlg.mQgsFileWidget_save_gpkg.fileChanged.connect(
            lambda: self.settings.setValue(QgsProject.instance().homePath(),
                                           self.dlg.mQgsFileWidget_save_gpkg.filePath()))

        self.dlg.mQgsFileWidget_search_gpkg.setFilePath(
            self.settings.value("", ""))
        self.dlg.mQgsFileWidget_search_gpkg.fileChanged.connect(
            lambda: self.settings.setValue("",
                                           self.dlg.mQgsFileWidget_search_gpkg.filePath()))

        # PhotoViewer360/settings/defaultPath

        self.dlg.mapLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dlg.mapLayerComboBox.setShowCrs(True)

    # def unload(self):
    #     """Unload Geo360 tool"""
    #     self.iface.removePluginMenu(u"&PhotoViewer360", self.action)
    #     self.iface.removeToolBarIcon(self.action)
    #     # Close server
    #     self.close_server()

    def unload(self):
        """Unload Geo360 tool"""
        for action in self.actions:
            self.iface.removePluginMenu(u"&PhotoViewer360", action)
            self.iface.removeToolBarIcon(action)
            # Close server
            self.close_server()

    # def is_running(self):
    #     return self.server_thread and self.server_thread.is_alive()

    def close_server(self):
        """Close Local server"""
        # Close server
        if self.server is not None:
            self.server.shutdown()
            time.sleep(1)
            self.server.server_close()
            while self.server_thread.is_alive():
                self.server_thread.join()
            self.server = None

    def make_server(self):
        """Create Local server"""
        # Close server
        self.close_server()
        # Create Server
        directory = (
                QgsApplication.qgisSettingsDirPath().replace("\\", "/")
                + "python/plugins/PhotoViewer360/viewer"
        )
        try:
            self.server = ThreadingHTTPServer(
                (config.IP, config.PORT),
                partial(QuietHandler, directory=directory),
            )
            self.server_thread = Thread(
                target=self.server.serve_forever, name="http_server"
            )
            self.server_thread.daemon = True
            print("Serving at port: %s" % self.server.server_address[1])
            time.sleep(1)
            self.server_thread.start()
        except Exception:
            print("Server Error")

    def run(self):
        "Run after pressing the plugin"

        self.dlg.show()

        coordinate_hotspot = self.slots.getHotSpotDetailsToPython()
        print("coordinate_hotspot: ", coordinate_hotspot)

    def click_feature(self):
        """Run click feature"""

        lys = QgsProject.instance().mapLayers().values()

        for layer in lys:
            # print("v: ", layer)
            # print("v.name(): ", layer.name())
            if layer.name() == self.useLayer:
                self.mapTool = SelectTool(self.iface, parent=self, layer=layer)
                self.iface.mapCanvas().setMapTool(self.mapTool)

                xform = QgsCoordinateTransform(QgsCoordinateReferenceSystem(layer.crs()),
                                               QgsCoordinateReferenceSystem(self.canvas.mapSettings().destinationCrs()),
                                               QgsProject.instance())
                self.canvas.setExtent(xform.transform(layer.extent()))
                self.canvas.refresh()
                print("self.useLayer: ", self.useLayer)

    def fromLayer_btn_clicked(self):
        self.is_press_button = True
        good_layer = False
        layer = self.dlg.mapLayerComboBox.currentText()
        self.useLayer = layer
        # print('Od razu praca na warstwie: ', layer.split(' ')[0])

        try:
            layer = QgsProject.instance().mapLayersByName(layer.split(' ')[0])[0]

            for field in layer.fields():
                if field.name() == 'sciezka_zdjecie':
                    good_layer = True

            if good_layer == True:
                self.mapTool = SelectTool(self.iface, parent=self, layer=layer)
                self.iface.mapCanvas().setMapTool(self.mapTool)

                xform = QgsCoordinateTransform(QgsCoordinateReferenceSystem(layer.crs()),
                                               QgsCoordinateReferenceSystem(self.canvas.mapSettings().destinationCrs()),
                                               QgsProject.instance())
                self.canvas.setExtent(xform.transform(layer.extent()))
                self.canvas.refresh()
                print("self.useLayer: ", self.useLayer)
                self.dlg.hide()
                self.click_feature()
            else:
                self.iface.messageBar().pushCritical("Ostrzeżenie:",
                                                     'Podana warstwa punktowa nie zawiera geotagowanych zdjęć')
                return False
        except IndexError:
            self.iface.messageBar().pushCritical("Ostrzeżenie:",
                                                 'Nie wskazano warstwy geopackage z geotagowanymi zdjęciami')
            return False

    def create_gpkg(self, photo_path, gpkg_path):
        """
        Creates GPKG based on image files
        """
        gpkg_path = os.path.join(gpkg_path)
        try:
            gpkg_temporary = processing.run("native:importphotos", {
                'FOLDER': photo_path,
                'RECURSIVE': False,
                'OUTPUT': gpkg_path})

        except:
            print("Tool Import Geotagged Photos failed!")
        gpkg_name = os.path.splitext(gpkg_path)[0]
        # gpkg_name = gpkg_path.split('\\')[-1].split('.')[0]
        print("----gpkg_name: ", gpkg_name)

        # vlayer = list(gpkg_temporary.values())[0]
        # QgsProject.instance().addMapLayer(vlayer)
        vlayer = QgsVectorLayer(gpkg_path, gpkg_name, "ogr")

        if not vlayer.isValid():
            print("Layer failed to load!")
        else:
            vlayer.startEditing()
            vlayer.dataProvider().addAttributes([QgsField("nr_drogi", QVariant.String),
                                                 QgsField("nazwa_ulicy", QVariant.String),
                                                 QgsField("numer_odcinka", QVariant.String),
                                                 QgsField("kilometraz", QVariant.String)])
            vlayer.updateFields()

            for field in vlayer.fields():
                # if field.name() == 'fid':
                #     self.rename_name_field(vlayer, 'fid', 'ID')
                if field.name() == 'photo':
                    self.rename_name_field(vlayer, 'photo', 'sciezka_zdjecie')
                elif field.name() == 'filename':
                    self.rename_name_field(vlayer, 'filename', 'nazwa_zdjecia')
                    print(field.name(), field.typeName())
                    features = vlayer.getFeatures()
                    for feature in features:
                        nazwa_zdjecia = feature["nazwa_zdjecia"]
                        try:
                            nr_drogi = nazwa_zdjecia.split("_")[0]
                            nazwa_ulicy = nazwa_zdjecia.split("_")[1]
                            numer_odcinka = nazwa_zdjecia.split("_")[2]
                            kilometraz = nazwa_zdjecia.split("_")[3]

                        except IndexError:
                            nr_drogi = nazwa_zdjecia
                            nazwa_ulicy = None
                            numer_odcinka = None
                            kilometraz = None

                        vlayer.dataProvider().changeAttributeValues(
                            {feature.id(): {vlayer.dataProvider().fieldNameMap()['nr_drogi']: nr_drogi}})
                        vlayer.dataProvider().changeAttributeValues(
                            {feature.id(): {vlayer.dataProvider().fieldNameMap()['nazwa_ulicy']: nazwa_ulicy}})
                        vlayer.dataProvider().changeAttributeValues(
                            {feature.id(): {vlayer.dataProvider().fieldNameMap()['numer_odcinka']: numer_odcinka}})
                        vlayer.dataProvider().changeAttributeValues(
                            {feature.id(): {vlayer.dataProvider().fieldNameMap()['kilometraz']: kilometraz}})

                elif field.name() == 'directory':
                    self.rename_name_field(vlayer, 'directory', 'nazwa_folderu')
                elif field.name() == 'altitude':
                    # self.rename_name_field(vlayer, 'altitude', 'wysokosc')
                    vlayer.dataProvider().deleteAttributes([4])
                    vlayer.updateFields()
                elif field.name() == 'direction':
                    self.rename_name_field(vlayer, 'direction', 'azymut')
                    features = vlayer.getFeatures()
                    for feature in features:
                        azymut_value = feature["azymut"]
                        # print(str(azymut_value.value()))
                        # print(type(str(azymut_value.value())))
                        if str(azymut_value.value()) == "NULL":
                            vlayer.dataProvider().changeAttributeValues(
                                {feature.id(): {vlayer.dataProvider().fieldNameMap()['azymut']: 310}})
                        else:
                            pass

                elif field.name() == 'rotation':
                    # self.rename_name_field(vlayer, 'rotation', 'obrot')
                    vlayer.dataProvider().deleteAttributes([5])
                    vlayer.updateFields()
                elif field.name() == 'longitude':
                    self.rename_name_field(vlayer, 'longitude', 'długosc geog')
                elif field.name() == 'latitude':
                    self.rename_name_field(vlayer, 'latitude', 'szerokosc geog')
                elif field.name() == 'timestamp':
                    self.rename_name_field(vlayer, 'timestamp', 'data_wykonania')
                    features = vlayer.getFeatures()
                    for feature in features:
                        data_value = feature["data_wykonania"]
                        if str(data_value) == "NULL":
                            sciezka_zdjecie_value = feature["sciezka_zdjecie"]
                            sciezka_zdjecie_value = sciezka_zdjecie_value.replace("\\", "/")
                            sciezka_zdjecie_open = open(sciezka_zdjecie_value, 'rb')
                            tags = exifread.process_file(sciezka_zdjecie_open)
                            # print("tag; ", tags)
                            self.dataTime = tags["EXIF DateTimeOriginal"]
                            vlayer.dataProvider().changeAttributeValues(
                                {feature.id(): {
                                    vlayer.dataProvider().fieldNameMap()['data_wykonania']: str(self.dataTime)}})
                            sciezka_zdjecie_open.close()
                    # pokombinować z bardziej wydajnym/optymalnym sposobem
        vlayer.commitChanges()
        return vlayer

    def usuniecie_warstwy_z_projektu(self, gpkg_path):
        lys = QgsProject.instance().mapLayers().values()
        for layer in lys:
            if layer.name() == gpkg_path.split('\\')[-1].split('.')[0]:
                QgsProject.instance().removeMapLayers([layer.id()])
                print("Usunięcie warstwy")

    def usuniecie_paczki_gpkg(self, gpkg_path):
        try:
            print("gpkg_path: ", gpkg_path)

            print("gpkg: ", gpkg_path)
            # os.remove(gpkg_path + "-shm")
            # os.remove(gpkg_path + "wal")
            # gpkg_path.close()
            os.remove(gpkg_path)

            print("Usunięcie pliku gpkg")
        # except PermissionError:
        #     print("FileNotFoundError")
        except FileNotFoundError:
            print("FileNotFoundError")
            pass
            # os.remove(gpkg_path)
            # print("Usunięcie pliku gpkg x2")

    def usuniecie_wartosci_gpkg(self, gpkg_path):

        lys = QgsProject.instance().mapLayers().values()
        for layer in lys:
            if layer.name() == gpkg_path.split('\\')[-1].split('.')[0]:
                print("layer.name(): ", layer.name())
                layer.startEditing()
                # liczba_objektow = layer.featureCount()
                for feat in layer.getFeatures():
                    layer.deleteFeature(feat.id())
                layer.commitChanges()
                print("commitChanges delete")

    def polaczenie_warstw(self, gpkg_path, overwrite):
        lys = QgsProject.instance().mapLayers().values()
        for layer in lys:
            if layer.name() == gpkg_path.split('\\')[-1].split('.')[0]:
                print("layer.name(): ", layer.name())
                layer.startEditing()
                for sourcefeat in overwrite.getFeatures():
                    newfeat = QgsFeature()
                    newfeat.setGeometry(sourcefeat.geometry())
                    newfeat.setAttributes(sourcefeat.attributes())
                    idx = overwrite.fields().indexFromName("fid")
                    if idx is not None:  # check if there is an "fid" attribute
                        newfeat[idx] = None  # clear attribute
                    layer.addFeature(newfeat)
                layer.commitChanges()

        print("importphotos and name layer nadpisane: ", layer.name())
        self.useLayer = str(layer.name())

    def nadpisanie_plik_button_clicked(self, photo_path, gpkg_path):
        print("nadpisanie gpkg")

        vlayer_overwrite = self.create_gpkg(photo_path, os.path.join(plugin_dir, 'temporary_files', 'overwrite.gpkg'))
        # vlayer_overwrite.setName(gpkg_path.split('\\')[-1].split('.')[0] + "_overwrite")
        # QgsProject.instance().addMapLayer(vlayer_overwrite)

        self.polaczenie_warstw(gpkg_path, vlayer_overwrite)

    def usuwanie_duplikatow(self, gpkg_path):
        # usuwanie duplikatów
        duplicate = processing.run("native:removeduplicatesbyattribute",
                                   {'INPUT': gpkg_path,
                                    'FIELDS': ['nazwa_zdjecia', 'długosc geog', 'szerokosc geog',
                                               'data_wykonania'],
                                    'OUTPUT': plugin_dir + "/temporary_files/no_duplicates.gpkg",
                                    'DUPLICATES': plugin_dir + "/temporary_files/duplicates.gpkg"})

        if duplicate['DUPLICATE_COUNT'] > 0:

            self.usuniecie_wartosci_gpkg(gpkg_path)

            layer_no_duplicate = QgsVectorLayer(duplicate['OUTPUT'], 'no_duplicate', 'ogr')
            self.polaczenie_warstw(gpkg_path, layer_no_duplicate)

            sciezka_zdjecie_list = []
            layer_duplicate = QgsVectorLayer(duplicate['DUPLICATES'], 'duplicate', 'ogr')
            for feat_duplic in layer_duplicate.getFeatures():
                sciezka_zdjecie_value = feat_duplic["nazwa_zdjecia"]
                sciezka_zdjecie_list.append(sciezka_zdjecie_value)

            if len(sciezka_zdjecie_list) <= 20:
                lista_zdjec = str(sciezka_zdjecie_list)
            else:
                lista_zdjec = str(sciezka_zdjecie_list[0:19]) + " ... "

            msgbox = QMessageBox(QMessageBox.Information, "Ostrzeżenie:",
                                 f"Usunięto {duplicate['DUPLICATE_COUNT']} duplikatów.\n\n"
                                 f"Duplikaty stwierdzono na podstawie atrybutów: "
                                 f"nazwa_zdjecia, długosc geog, szerokosc geog, data_wykonania.\n\n"
                                 f"Stwierdzono duplikaty zdjęć: \n"
                                 f"{lista_zdjec}")
            msgbox.exec_()

    def fromPhotos_btn_clicked(self):
        self.is_press_button = True

        photo_path = os.path.join(self.dlg.mQgsFileWidget_search_photo.filePath())
        if not self.checkSavePath(photo_path):
            return False

        gpkg_path = self.dlg.mQgsFileWidget_save_gpkg.filePath()
        if gpkg_path.find('.gpkg') != -1:
            pass
        else:
            print("dopisanie rozszerzenia")
            gpkg_path = gpkg_path + '.gpkg'

        """ Pasek postępu"""
        # progressMessageBar = self.iface.messageBar().createMessage("Postęp importowania " + gpkg_path.split("\\")[-1] + "...")
        # progress = QProgressBar()
        # progress.setMaximum(100)
        # progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # progressMessageBar.layout().addWidget(progress)
        # self.iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
        # progress.setValue()

        if not gpkg_path:
            self.iface.messageBar().pushCritical("Ostrzeżenie:",
                                                 'Nie wskazano wskazano miejsca zapisu plików')
            return False
        elif os.path.exists(gpkg_path):
            msgBox = QMessageBox(QMessageBox.Information, "Informacja",
                                 "Plik już istnieje.\n"
                                 "Czy chcesz stworzyć nowy plik (stary plik GPKG zostanie usunięty)?\n"
                                 "Czy chcesz nadpisać stary plik?")
            nowy_plik_button = msgBox.addButton('Nowy plik', QtWidgets.QMessageBox.ApplyRole)
            nadpisanie_plik_button = msgBox.addButton('Nadpisanie starego pliku', QtWidgets.QMessageBox.ApplyRole)
            anuluj_button = msgBox.addButton('Anuluj', QtWidgets.QMessageBox.ResetRole)
            msgBox.exec_()

            if msgBox.clickedButton() == nowy_plik_button:
                # self.usuniecie_warstwy_z_projektu(gpkg_path)
                self.usuniecie_wartosci_gpkg(gpkg_path)
                self.nadpisanie_plik_button_clicked(photo_path, gpkg_path)

                self.dlg.hide()
                self.click_feature()
            elif msgBox.clickedButton() == nadpisanie_plik_button:
                self.nadpisanie_plik_button_clicked(photo_path, gpkg_path)
                # self.usuwanie_duplikatow(gpkg_path)

                duplicate = processing.run("native:removeduplicatesbyattribute",
                                           {'INPUT': gpkg_path,
                                            'FIELDS': ['nazwa_zdjecia', 'długosc geog', 'szerokosc geog',
                                                       'data_wykonania'],
                                            'OUTPUT': plugin_dir + "/temporary_files/no_duplicates.gpkg",
                                            'DUPLICATES': plugin_dir + "/temporary_files/duplicates.gpkg"})

                if duplicate['DUPLICATE_COUNT'] > 0:

                    self.usuniecie_wartosci_gpkg(gpkg_path)

                    layer_no_duplicate = QgsVectorLayer(duplicate['OUTPUT'], 'no_duplicate', 'ogr')
                    self.polaczenie_warstw(gpkg_path, layer_no_duplicate)

                    sciezka_zdjecie_list = []
                    layer_duplicate = QgsVectorLayer(duplicate['DUPLICATES'], 'duplicate', 'ogr')
                    for feat_duplic in layer_duplicate.getFeatures():
                        sciezka_zdjecie_value = feat_duplic["nazwa_zdjecia"]
                        sciezka_zdjecie_list.append(sciezka_zdjecie_value)

                    if len(sciezka_zdjecie_list) <= 20:
                        lista_zdjec = str(sciezka_zdjecie_list)
                    else:
                        lista_zdjec = str(sciezka_zdjecie_list[0:19]) + " ... "

                    msgbox = QMessageBox(QMessageBox.Information, "Ostrzeżenie:",
                                         f"Usunięto {duplicate['DUPLICATE_COUNT']} duplikatów.\n\n"
                                         f"Duplikaty stwierdzono na podstawie atrybutów: "
                                         f"nazwa_zdjecia, długosc geog, szerokosc geog, data_wykonania.\n\n"
                                         f"Stwierdzono duplikaty zdjęć: \n"
                                         f"{lista_zdjec}")
                    msgbox.exec_()

                self.dlg.hide()
                self.click_feature()
            elif msgBox.clickedButton() == anuluj_button:
                return False
            else:
                pass

        else:
            vlayer = self.create_gpkg(photo_path, gpkg_path)
            # vlayer = QgsVectorLayer(vlayer, gpkg_path.split('\\')[-1].split('.')[0], "ogr")
            # QgsVectorFileWriter.writeAsVectorFormat(vlayer, gpkg_path, "utf-8", vlayer.crs(), "GeoPackage")
            QgsProject.instance().addMapLayer(vlayer)
            print("importphotos and name layer: ", vlayer.name())
            self.useLayer = str(vlayer.name())
            self.dlg.hide()
            self.click_feature()

    def fromGPKG_btn_clicked(self):
        self.is_press_button = True
        gpkg_path = os.path.join(self.dlg.mQgsFileWidget_search_gpkg.filePath())
        if not self.checkSavePath(gpkg_path):
            return False
        gpkg_name = os.path.splitext(gpkg_path)[0]
        # gpkg_name = gpkg_path.split('\\')[-1].split('.')[0]
        print("ppp-gpkg_name: ", gpkg_name)

        vlayer = QgsVectorLayer(gpkg_path, gpkg_name, "ogr")
        if not vlayer.isValid():
            print("Layer failed to load!")
        else:
            QgsProject.instance().addMapLayer(vlayer)

        print("importphotos and name layer: ", vlayer.name())
        self.useLayer = vlayer.name()
        self.dlg.hide()
        self.click_feature()

    def rename_name_field(self, rlayer, oldname, newname):
        findex = rlayer.dataProvider().fieldNameIndex(oldname)
        if findex != -1:
            rlayer.dataProvider().renameAttributes({findex: newname})
            rlayer.updateFields()

    def ShowViewer(self, featuresId=None, layer=None):
        """Run dialog Geo360"""
        self.featuresId = featuresId
        self.layer = layer
        print("ShowViewer")
        if self.orbitalViewer and not self.is_press_button:
            self.orbitalViewer.ReloadView(self.featuresId)
            print("ShowViewer orbitalViewer is NOT None")
        else:
            if self.orbitalViewer and self.is_press_button:
                self.is_press_button = False
                self.canvas.refresh()
                print("ShowViewer button was pressed")
            self.orbitalViewer = Geo360Dialog(
                self.iface, parent=self, featuresId=featuresId, layer=self.layer, name_layer=self.useLayer,
                press_button=self.is_press_button
            )
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.orbitalViewer)

    def checkSavePath(self, path):
        """Sprawdza czy ścieżka jest poprawna i zwraca Boolean"""
        if not path or path == '':
            QMessageBox(QMessageBox.Warning, "Ostrzeżenie:", 'Nie wskazano ścieżki do pliku/folderu').exec_()
            return False
        elif not os.path.exists(path):
            QMessageBox(QMessageBox.Warning, "Ostrzeżenie:", 'Wskazano nieistniejącą ścieżkę do odczytu plików/folderu').exec_()
            return False
        else:
            return True


class SelectTool(QgsMapToolIdentify):
    """Select Photo on map"""

    def __init__(self, iface, parent=None, layer=None):
        QgsMapToolIdentify.__init__(self, iface.mapCanvas())
        self.canvas = iface.mapCanvas()
        self.iface = iface
        self.layer = layer
        self.parent = parent

        self.cursor = QCursor(
            QPixmap(
                [
                    "16 16 3 1",
                    "      c None",
                    ".     c #FF0000",
                    "+     c #FFFFFF",
                    "                ",
                    "       +.+      ",
                    "      ++.++     ",
                    "     +.....+    ",
                    "    +.     .+   ",
                    "   +.   .   .+  ",
                    "  +.    .    .+ ",
                    " ++.    .    .++",
                    " ... ...+... ...",
                    " ++.    .    .++",
                    "  +.    .    .+ ",
                    "   +.   .   .+  ",
                    "   ++.     .+   ",
                    "    ++.....+    ",
                    "      ++.++     ",
                    "       +.+      ",
                ]
            )
        )

    def activate(self):
        self.canvas.setCursor(self.cursor)

    def canvasReleaseEvent(self, event):
        # print("canvasReleaseEvent")
        found_features = self.identify(
            event.x(), event.y(), [self.layer], self.TopDownAll
        )

        if len(found_features) > 0:
            layer = found_features[0].mLayer
            feature = found_features[0].mFeature
            # Zoom To Feature
            qgsutils.zoomToFeature(self.canvas, layer, feature.id())
            self.parent.ShowViewer(featuresId=feature.id(), layer=layer)
