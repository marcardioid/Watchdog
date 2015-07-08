#!/usr/bin/python
# Creates a task-bar icon.  Run from Python.exe to see the
# messages printed.

import win32api, win32gui
import win32con, winerror
import win32file, win32event
import sys, os
import subprocess
import threading
import time
import logging

class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopnow = False

    def run(self):
        with open("config.ini") as file:
            directories = file.read().splitlines()
            path_to_watch = directories[0]
        print("Started watching '%s' at '%s'." % ("".join(path_to_watch), time.asctime()))

        change_handle = win32file.FindFirstChangeNotification(
          path_to_watch,
          0,
          win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        )

        # run once on startup
        subprocess.call("python.exe watchdog.py")

        try:
          while 1 and not self.stopnow:
            result = win32event.WaitForSingleObject(change_handle, 500)

            if result == win32con.WAIT_OBJECT_0:
              time.sleep(1) # hack around 'access denied' errors
              subprocess.call("python.exe watchdog.py")
              win32file.FindNextChangeNotification(change_handle)
        finally:
          win32file.FindCloseChangeNotification(change_handle)
          print("Stopped watching '%s' at '%s'." % ("".join (path_to_watch), time.asctime()))

    def stop(self):
        self.stopnow = True

class MainWindow:
    def __init__(self):
        msg_TaskbarRestart = win32gui.RegisterWindowMessage("TaskbarCreated");
        message_map = {
                msg_TaskbarRestart: self.OnRestart,
                win32con.WM_DESTROY: self.OnDestroy,
                win32con.WM_COMMAND: self.OnCommand,
                win32con.WM_USER+20: self.OnTaskbarNotify,
        }
        # Register the Window class.
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "Watchdog"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        wc.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW )
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map

        # Don't blow up if class already registered to make testing easier
        try:
            classAtom = win32gui.RegisterClass(wc)
        except win32gui.error as err_info:
            if err_info.winerror != winerror.ERROR_CLASS_ALREADY_EXISTS:
                raise

        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(wc.lpszClassName, "Watchdog", style, \
                0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, \
                0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        self._DoCreateIcons()

        # Start the Worker
        self.bgp = Worker()
        self.bgp.setDaemon(True)
        self.bgp.start()

    def _DoCreateIcons(self):
        hinst =  win32api.GetModuleHandle(None)
        iconPathName = os.path.abspath(os.path.join(os.getcwd(), "watchdog.ico"))
        if os.path.isfile(iconPathName):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            print("Can't find an icon file. Using system default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, "Watchdog")
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except win32gui.error:
            print("Waiting for explorer to start...")

    def OnRestart(self, hwnd, msg, wparam, lparam):
        self._DoCreateIcons()

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)

    def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONUP or lparam==win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "Settings")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1024, "Refresh")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1025, "Exit")
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return 1

    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        if id == 1023:
            import webbrowser
            webbrowser.open("exceptions.ini")
        elif id == 1024:
            self.bgp.stop()
            self.bgp.join()
            self.bgp = Worker()
            self.bgp.setDaemon(True)
            self.bgp.start()
        elif id == 1025:
            self.bgp.stop()
            self.bgp.join()
            win32gui.DestroyWindow(self.hwnd)
        else:
            print("Unknown command -", id)

def main():
    logging.basicConfig(level=logging.DEBUG, filename="watchdog.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    w = MainWindow()
    win32gui.PumpMessages()

if __name__ == "__main__":
    main()