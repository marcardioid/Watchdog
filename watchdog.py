#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import sys
import os
import time
import atexit
import re
import configparser
import utils
from plexapi.server import PlexServer
from scanner import Scanner

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        uic.loadUi("design.ui", self)
        icon = QtGui.QIcon("watchdog.ico")
        self.setWindowIcon(icon)
        self.setWindowTitle("Watchdog")

        self.isSystemTrayAvailable = QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()
        if self.isSystemTrayAvailable:
            self.tray = QtWidgets.QSystemTrayIcon(self)
            self.tray.setIcon(icon)
            self.tray.setToolTip("Watchdog")
            self.tray_populate()
            self.tray.activated.connect(self.trayEvent)
            self.tray.show()

        self.buttonBrowseInput.clicked.connect(lambda: self.browse_directory(self.comboboxInput))
        self.buttonBrowseOutputTVS.clicked.connect(lambda: self.browse_directory(self.comboboxOutputTVS))
        self.buttonBrowseOutputMOV.clicked.connect(lambda: self.browse_directory(self.comboboxOutputMOV))
        self.buttonToggle.clicked.connect(self.toggle)
        self.buttonSave.clicked.connect(self.save_settings)
        self.buttonRefresh.clicked.connect(self.refresh)
        self.buttonNewException.clicked.connect(lambda: self.add_exception("", ""))

        self.progressBar.setRange(0, 0)
        sp = self.progressBar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.progressBar.setSizePolicy(sp)
        self.progressBar.setVisible(False)

        self.load_settings()

        self.watching = False
        self.scanner = Scanner(True)
        self.scanner.message.connect(self.add_output)

    def browse_directory(self, combobox):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Pick a folder")
        if directory:
            if combobox.findText(directory) == -1:
                combobox.addItem(directory)
            combobox.setCurrentIndex(combobox.findText(directory))

    def add_output(self, output):
        self.listOutput.addItem(output)

    def add_exception(self, old, new):
        te = self.tableExceptions
        tr = te.rowCount()
        te.insertRow(tr)
        te.setItem(tr, 0, QtWidgets.QTableWidgetItem(old))
        te.setItem(tr, 1, QtWidgets.QTableWidgetItem(new))
        tb = QtWidgets.QPushButton("DEL")
        tb.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        tb.clicked.connect(lambda: te.removeRow([i for i in range(0, te.rowCount()) if te.cellWidget(i, 2) == tb][0]))
        te.setCellWidget(tr, 2, tb)

    def load_settings(self):
        self.add_output("Loading settings...")
        directories = utils.loadConfig()
        comboboxes = [self.comboboxInput, self.comboboxOutputTVS, self.comboboxOutputMOV]
        for i, dir in enumerate(directories):
            if comboboxes[i].findText(dir) == -1:
                comboboxes[i].addItem(dir)
            comboboxes[i].setCurrentIndex(comboboxes[i].findText(dir))
        config = configparser.ConfigParser()
        config.read("config/settings.ini")
        self.lineFormatTVS.setText(config["FORMATS"]["formattvs"])
        self.lineFormatTVS.setEnabled(False) # TODO: ENABLE FUNCTIONALITY
        self.lineFormatMOV.setText(config["FORMATS"]["formatmov"])
        self.lineFormatMOV.setEnabled(False) # TODO: ENABLE FUNCTIONALITY
        mediaserver = config["GENERAL"]["mediaserver"]
        if self.comboboxMediaServer.findText(mediaserver) == -1:
            self.comboboxMediaServer.addItem(mediaserver)
        self.comboboxMediaServer.setCurrentIndex(self.comboboxMediaServer.findText(mediaserver))
        self.comboboxMediaServer.setEnabled(False) # TODO: ENABLE FUNCTIONALITY
        self.checkboxCleanup.setChecked(config.getboolean("GENERAL", "cleanup"))
        self.checkboxOverwrite.setChecked(config.getboolean("GENERAL", "overwrite"))
        self.checkboxMinimized.setChecked(config.getboolean("GENERAL", "startmin"))
        self.checkboxDebug.setChecked(config.getboolean("GENERAL", "debug"))
        self.add_output("Done.")
        self.load_exceptions()

    def save_settings(self):
        if self.watching:
            self.stop()
        self.add_output("Saving settings...")
        config = configparser.ConfigParser()
        config.read("config/settings.ini")
        config["DIRECTORIES"]["input"] = self.comboboxInput.currentText()
        config["DIRECTORIES"]["outputtvs"] = self.comboboxOutputTVS.currentText()
        config["DIRECTORIES"]["outputmov"] = self.comboboxOutputMOV.currentText()
        config["FORMATS"]["formattvs"] = self.lineFormatTVS.text()
        config["FORMATS"]["formatmov"] = self.lineFormatMOV.text()
        config["GENERAL"]["mediaserver"] = self.comboboxMediaServer.currentText()
        config["GENERAL"]["cleanup"] = str(self.checkboxCleanup.isChecked())
        config["GENERAL"]["overwrite"] = str(self.checkboxOverwrite.isChecked())
        config["GENERAL"]["startmin"] = str(self.checkboxMinimized.isChecked())
        config["GENERAL"]["debug"] = str(self.checkboxDebug.isChecked())
        with open("config/settings.ini", "w") as file:
            config.write(file)
        self.add_output("Done.")
        self.save_exceptions()

    def load_exceptions(self):
        self.add_output("Loading exceptions...")
        with open("config/exceptions.ini", "r") as file:
            lines = file.read().splitlines()
        for line in lines:
            if line.count(';') == 1:
                exception = re.match(r"(.*);(.*)", line)
                if exception:
                    old, new = exception.group(1), exception.group(2)
                    self.add_exception(old, new)
                    self.add_output("Added exception '{}' => '{}'.".format(old, new))
            else:
                self.add_output("Failed saving exception '{}' => '{}': illegal character!".format(old, new))
        self.add_output("Done.")

    def save_exceptions(self):
        self.add_output("Saving exceptions...")
        te = self.tableExceptions
        with open("config/exceptions.ini", "w") as file:
            for i in range(0, te.rowCount()):
                old, new = te.item(i, 0).text(), te.item(i, 1).text()
                if len(old) > 1 and len(new) > 1:
                    exception = "{};{}".format(old, new)
                    if exception.count(';') == 1:
                        file.writelines("{}\n".format(exception.rstrip()))
                    else:
                        self.add_output("Failed saving exception '{}' => '{}': illegal character!".format(old, new))
        self.add_output("Done.")

    def tray_populate(self):
        menu = QtWidgets.QMenu(self)
        # menu.addAction(QtWidgets.QAction("Minimize", self, triggered=self.hide))
        # menu.addAction(QtWidgets.QAction("Restore", self, triggered=self.showNormal))
        menu.addAction(QtWidgets.QAction("Toggle", self, triggered=self.toggle))
        # menu.addSeparator()
        menu.addAction(QtWidgets.QAction("Quit", self, triggered=QtWidgets.QApplication.instance().quit))
        self.tray.setContextMenu(menu)

    def show_message(self, message):
        self.add_output(message)
        if self.isSystemTrayAvailable and self.tray.isVisible():
            self.tray.showMessage("Watchdog", message, QtWidgets.QSystemTrayIcon.MessageIcon(QtWidgets.QSystemTrayIcon.Information), 10 * 1000)
        else:
            QtWidgets.QMessageBox.information(self, "Watchdog", message)

    def start(self):
        self.scanner.start()
        self.progressBar.setVisible(True)
        self.buttonToggle.setText("Stop")
        self.watching = True
        self.buttonSave.setEnabled(False)
        self.buttonRefresh.setEnabled(False)

    def stop(self):
        self.scanner.stop()
        self.scanner.wait()
        self.scanner = Scanner(True)
        self.scanner.message.connect(self.add_output)
        self.progressBar.setVisible(False)
        self.buttonToggle.setText("Start")
        self.watching = False
        self.buttonSave.setEnabled(True)
        self.buttonRefresh.setEnabled(True)

    def toggle(self):
        if self.watching:
            self.stop()
        else:
            self.start()

    def refresh(self):
        plex = PlexServer()
        plex.library.refresh()
        self.add_output("Refreshed Plex.")


    def trayEvent(self, event):
        if event in [QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick]:
            self.showNormal()

    def closeEvent(self, event):
        if self.isSystemTrayAvailable:
            self.tray.show()
            if self.tray.isVisible():
                self.hide()
                event.ignore()


def onexit():
    window.stop()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("fusion")
    window = MainWindow()
    config = configparser.ConfigParser()
    config.read("config/settings.ini")
    if not config.getboolean("GENERAL", "startmin"):
        window.show()
    atexit.register(onexit)
    sys.exit(app.exec())
