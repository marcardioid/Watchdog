#!/usr/bin/python

import sys
import atexit
import re
from scanner import Scanner
import utils
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtCore import QDir, QModelIndex
from PyQt5.QtWidgets import (QWidget, QAction, QApplication, QComboBox,
        QGridLayout, QHBoxLayout, QLabel, QMessageBox, QMenu, QPushButton,
        QSystemTrayIcon, QSizePolicy, QFileDialog, QGroupBox, QTableView, QProgressBar)

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        # GUI
        if isSystemTrayAvailable:
            self.createActions()
            self.createTrayIcon()
            self.trayIcon.activated.connect(self.iconActivated)

        self.inputDirLabel = QLabel("Input Directory:")
        self.outputDirTVSLabel = QLabel("Output Directory (Shows):")
        self.outputDirMOVLabel = QLabel("Output Directory (Movies):")
        self.inputDirComboBox = self.createComboBox()
        self.outputDirTVSComboBox = self.createComboBox()
        self.outputDirMOVComboBox = self.createComboBox()
        self.inputDirButton = self.createButton("&Browse", lambda: self.browse(self.inputDirComboBox))
        self.outputDirTVSButton = self.createButton("&Browse", lambda: self.browse(self.outputDirTVSComboBox))
        self.outputDirMOVButton = self.createButton("&Browse", lambda: self.browse(self.outputDirMOVComboBox))

        self.sourceGroupBox = QGroupBox("Manage Exceptions")
        self.model = QStandardItemModel(0, 3)
        self.model.setHorizontalHeaderLabels(["OLD NAME", "NEW NAME", "MANAGE"])
        self.list = QTableView()
        self.list.setModel(self.model)
        self.list.setAlternatingRowColors(True)
        self.list.horizontalHeader().setStretchLastSection(True)
        self.list.resizeRowsToContents()
        self.list.setColumnWidth(0, 250)
        self.list.setColumnWidth(1, 250)

        self.insertButton = self.createButton("&Insert", self.insertRow)
        self.toggleButton = self.createButton("&Start Watching", self.toggle)
        self.toggleButton.setFixedSize(100, 23)
        self.saveButton = self.createButton("&Save", self.save)
        self.busyBar = QProgressBar()
        self.busyBar.setRange(0, 0)
        self.busyBar.setToolTip("Watching for new files...")
        self.busyBar.hide()

        sourceLayout = QGridLayout()
        sourceLayout.addWidget(self.list)
        sourceLayout.addWidget(self.insertButton)
        self.sourceGroupBox.setLayout(sourceLayout)

        # LAYOUT
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.busyBar)
        buttonsLayout.addWidget(self.toggleButton)
        buttonsLayout.addWidget(self.saveButton)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.inputDirLabel, 0, 0)
        mainLayout.addWidget(self.inputDirComboBox, 0, 1)
        mainLayout.addWidget(self.inputDirButton, 0, 2)
        mainLayout.addWidget(self.outputDirTVSLabel, 1, 0)
        mainLayout.addWidget(self.outputDirTVSComboBox, 1, 1)
        mainLayout.addWidget(self.outputDirTVSButton, 1, 2)
        mainLayout.addWidget(self.outputDirMOVLabel, 2, 0)
        mainLayout.addWidget(self.outputDirMOVComboBox, 2, 1)
        mainLayout.addWidget(self.outputDirMOVButton, 2, 2)
        mainLayout.addWidget(self.sourceGroupBox, 4, 0, 2, 3)
        mainLayout.addLayout(buttonsLayout, 6, 0, 1, 3)
        self.setLayout(mainLayout)

        self.setIcon('watchdog.ico')
        self.setWindowTitle("Watchdog - Finds, renames and moves your media files.")
        self.setFixedSize(640, 360)

        # Start the Worker
        self.watching = False
        self.scanner = Scanner(True)

    def setVisible(self, visible):
        if isSystemTrayAvailable:
            self.minimizeAction.setEnabled(visible)
            self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(Window, self).setVisible(visible)

    def showNormal(self):
        self.trayIcon.hide()
        super(Window, self).showNormal()

    def closeEvent(self, event):
        if isSystemTrayAvailable:
            self.trayIcon.show()
            if self.trayIcon.isVisible():
                self.showMessage("App is still running in your system tray.")
                self.hide()
                event.ignore()

    def setIcon(self, filename):
        icon = QIcon(filename)
        self.setWindowIcon(icon)
        if isSystemTrayAvailable:
            self.trayIcon.setIcon(icon)
            self.trayIcon.setToolTip("Watchdog")

    def iconActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showNormal()

    def showMessage(self, message):
        if isSystemTrayAvailable and self.trayIcon.isVisible():
            self.trayIcon.showMessage("Watchdog",
                    message,
                    QSystemTrayIcon.MessageIcon(QSystemTrayIcon.Information),
                    10 * 1000)
        else:
            QMessageBox.information(self, "Watchdog", message)

    def createComboBox(self):
        comboBox = QComboBox()
        comboBox.setEditable(True)
        comboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return comboBox

    def createButton(self, text, member):
        button = QPushButton(text)
        button.clicked.connect(member)
        return button

    def createActions(self):
        self.minimizeAction = QAction("Mi&nimize", self, triggered=self.hide)
        self.restoreAction = QAction("&Restore", self,
                triggered=self.showNormal)
        self.toggleAction = QAction("&Toggle", self, triggered=self.toggle)
        self.quitAction = QAction("&Quit", self,
                triggered=QApplication.instance().quit)

    def createTrayIcon(self):
         self.trayIconMenu = QMenu(self)
         self.trayIconMenu.addAction(self.minimizeAction)
         self.trayIconMenu.addAction(self.restoreAction)
         self.trayIconMenu.addAction(self.toggleAction)
         self.trayIconMenu.addSeparator()
         self.trayIconMenu.addAction(self.quitAction)

         self.trayIcon = QSystemTrayIcon(self)
         self.trayIcon.setContextMenu(self.trayIconMenu)

    def insertRow(self):
        item = QStandardItem('')
        self.model.appendRow([item, QStandardItem('')])
        itemindex = self.model.indexFromItem(item).row()
        self.insertWidget(itemindex, item)

    def deleteRow(self, n):
        print("DELETING " + str(n))
        self.model.removeRow(n)

    def insertWidget(self, n, item):
        node_widget = QPushButton("DELETE")
        node_widget.clicked.connect(lambda: self.deleteRow(self.model.indexFromItem(item).row()))
        qindex_widget = self.model.index(n, 2, QModelIndex())
        self.list.setIndexWidget(qindex_widget, node_widget)

    def browse(self, combobox):
        directory = QFileDialog.getExistingDirectory(self, "Find Files", QDir.currentPath())
        if directory:
            if combobox.findText(directory) == -1:
                combobox.addItem(directory)
            combobox.setCurrentIndex(combobox.findText(directory))

    def save(self):
        if self.scanner.isAlive():
            self.toggle()
        inputDir = self.inputDirComboBox.currentText()
        outputDirTVS = self.outputDirTVSComboBox.currentText()
        outputDirMOV = self.outputDirMOVComboBox.currentText()
        with open("config.ini", "w") as file:
            file.write(inputDir + "\n" + outputDirTVS + "\n" + outputDirMOV)
        exceptions = []
        with open("exceptions.ini", "r") as file:
            exceptions += file.readlines()[:2]
        for i in range(self.model.rowCount()):
            itemOld = self.model.item(i, 0)
            itemNew = self.model.item(i ,1)
            exceptions.append(itemOld.text() + ";" + itemNew.text())
        with open("exceptions.ini", "w") as file:
            for ex in exceptions:
                if len(ex) > 1:
                    file.write(ex.rstrip() + '\n')
        self.showMessage("Saved configuration.")
        self.scanner = Scanner(True)

    def createTable(self):
        exceptions = utils.loadExceptions()
        i = 0
        for k, v in exceptions.items():
            itemOld = QStandardItem(k)
            itemNew = QStandardItem(v)
            self.model.appendRow([itemOld, itemNew])
            self.insertWidget(i, itemOld)
            i += 1

    def load(self):
        directories = utils.loadConfig()
        comboboxes = [self.inputDirComboBox, self.outputDirTVSComboBox, self.outputDirMOVComboBox]
        if len(directories) == 3:
            for i, directory in enumerate(directories):
                if comboboxes[i].findText(directory) == -1:
                    comboboxes[i].addItem(directory)
                comboboxes[i].setCurrentIndex(comboboxes[i].findText(directory))
        else:
            pass
        self.createTable()

    def toggle(self):
        if not self.watching:
            self.scanner.setDaemon(True)
            self.scanner.start()
            self.busyBar.show()
        else:
            if self.scanner.isAlive():
                self.scanner.stop()
                self.scanner.join()
            self.scanner = Scanner(True)
            self.busyBar.hide()
        self.watching = not self.watching
        self.toggleButton.setText("Stop Watching" if self.watching else "Start Watching")

    def stop(self):
        if self.scanner.isAlive():
            self.scanner.stop()
            self.scanner.join()

def exitHandler():
    window.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    isSystemTrayAvailable = QSystemTrayIcon.isSystemTrayAvailable()
    app.setQuitOnLastWindowClosed(not isSystemTrayAvailable)

    window = Window()
    window.show()
    window.load()

    atexit.register(exitHandler)
    sys.exit(app.exec_())