#!/usr/bin/python

import win32con, win32file, win32event
import threading
import time
import os
import renamer
import utils


class Scanner(threading.Thread):
    def __init__(self, verbose=False):
        threading.Thread.__init__(self)
        self.abort = False
        self.verbose = verbose

    def run(self):
        directories = utils.loadConfig()
        dir_src, dir_tvs, dir_mov = os.path.normpath(directories[0]), os.path.normpath(directories[1]), os.path.normpath(directories[2])
        if self.verbose:
            print("Started watching '{}' at '{}'.".format(str(dir_src), time.asctime()))

        change_handle = win32file.FindFirstChangeNotification(
          dir_src,
          0,
          win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        )

        # run once on startup
        renamer.main(dir_src, dir_tvs, dir_mov)

        # then loop
        try:
            while True and not self.abort:
                result = win32event.WaitForSingleObject(change_handle, 500)
                if result == win32con.WAIT_OBJECT_0:
                    time.sleep(1)
                    renamer.main(dir_src, dir_tvs, dir_mov)
                    win32file.FindNextChangeNotification(change_handle)
        finally:
            win32file.FindCloseChangeNotification(change_handle)
            if self.verbose:
                print("Stopped watching '{}' at '{}'.".format(str(dir_src), time.asctime()))

    def stop(self):
        self.abort = True
