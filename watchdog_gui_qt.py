#!/usr/bin/python

import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDir, QFile
from PyQt5.QtWidgets import (QAction, QApplication, QComboBox,
        QDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
        QMenu, QPushButton, QSystemTrayIcon, QSizePolicy, QFileDialog)
from scanner import Scanner
import atexit

class Window(QDialog):
    def __init__(self):
        super(Window, self).__init__()

        # GUI
        self.createActions()
        self.createTrayIcon()
        self.inputDirLabel = QLabel("Input Directory:")
        self.outputDirTVSLabel = QLabel("Output Directory (Shows):")
        self.outputDirMOVLabel = QLabel("Output Directory (Movies):")
        self.inputDirComboBox = self.createComboBox()
        self.outputDirTVSComboBox = self.createComboBox()
        self.outputDirMOVComboBox = self.createComboBox()
        self.inputDirButton = self.createButton("&Browse", lambda: self.browse(self.inputDirComboBox))
        self.outputDirTVSButton = self.createButton("&Browse", lambda: self.browse(self.outputDirTVSComboBox))
        self.outputDirMOVButton = self.createButton("&Browse", lambda: self.browse(self.outputDirMOVComboBox))
        self.saveButton = self.createButton("&Save", self.save)
        self.exceptionsButton = self.createButton("&Manage Exeptions", self.manageExceptions)

        # HANDLERS
        self.trayIcon.activated.connect(self.iconActivated)

        # LAYOUT
        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.exceptionsButton)
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
        mainLayout.addLayout(buttonsLayout, 5, 0, 1, 3)
        self.setLayout(mainLayout)

        self.setIcon('watchdog.ico')
        self.setWindowTitle("Watchdog")
        self.setFixedSize(700, 150)

        # Start the Worker
        self.bgp = Scanner(True)
        self.bgp.setDaemon(True)
        self.bgp.start()

    def setVisible(self, visible):
        self.minimizeAction.setEnabled(visible)
        self.restoreAction.setEnabled(self.isMaximized() or not visible)
        super(Window, self).setVisible(visible)

    def showNormal(self):
        self.trayIcon.hide()
        super(Window, self).showNormal()

    def closeEvent(self, event):
        self.trayIcon.show()
        if self.trayIcon.isVisible():
            self.showMessage()
            self.hide()
            event.ignore()

    def setIcon(self, filename):
        icon = QIcon(filename)
        self.trayIcon.setIcon(icon)
        self.setWindowIcon(icon)
        self.trayIcon.setToolTip("Watchdog")

    def iconActivated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showNormal()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.showMessage()

    def showMessage(self):
        self.trayIcon.showMessage("Still running!",
                "Watchdog is still running in your system tray.",
                QSystemTrayIcon.MessageIcon(QSystemTrayIcon.Information),
                10 * 1000)

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
        self.quitAction = QAction("&Quit", self,
                triggered=QApplication.instance().quit)

    def createTrayIcon(self):
         self.trayIconMenu = QMenu(self)
         self.trayIconMenu.addAction(self.minimizeAction)
         self.trayIconMenu.addAction(self.restoreAction)
         self.trayIconMenu.addSeparator()
         self.trayIconMenu.addAction(self.quitAction)

         self.trayIcon = QSystemTrayIcon(self)
         self.trayIcon.setContextMenu(self.trayIconMenu)

    def browse(self, combobox):
        directory = QFileDialog.getExistingDirectory(self, "Find Files", QDir.currentPath())
        if directory:
            if combobox.findText(directory) == -1:
                combobox.addItem(directory)
            combobox.setCurrentIndex(combobox.findText(directory))

    def manageExceptions(self):
        import webbrowser
        webbrowser.open("exceptions.ini")

    def save(self):
        self.bgp.stop()
        self.bgp.join()
        inputDir = self.inputDirComboBox.currentText()
        outputDirTVS = self.outputDirTVSComboBox.currentText()
        outputDirMOV = self.outputDirMOVComboBox.currentText()
        with open("config.ini", "w") as file:
            file.write(inputDir + "\n" + outputDirTVS + "\n" + outputDirMOV)
        self.bgp = Scanner(True)
        self.bgp.setDaemon(True)
        self.bgp.start()
        # print("SAVED CONFIG")

    def load(self):
        with open("config.ini") as file:
            directories = file.read().splitlines()
        comboboxes = [self.inputDirComboBox, self.outputDirTVSComboBox, self.outputDirMOVComboBox]
        if len(directories) >= 3:
            for i, directory in enumerate(directories):
                if comboboxes[i].findText(directory) == -1:
                    comboboxes[i].addItem(directory)
                comboboxes[i].setCurrentIndex(comboboxes[i].findText(directory))
            # print("LOADED CONFIG")
        else:
            print("COULD NOT LOAD CONFIG")

    def stop(self):
        self.bgp.stop()
        self.bgp.join()

def exitHandler():
    window.stop()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Watchdog",
                "Couldn't detect system tray on this system.\nExiting...")
        sys.exit(1)

    QApplication.setQuitOnLastWindowClosed(False)

    window = Window()
    window.show()
    window.load()

    atexit.register(exitHandler)
    sys.exit(app.exec_())