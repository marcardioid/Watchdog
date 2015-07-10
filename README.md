# Watchdog
Python app that watches a directory and finds any media files in it.<br>
Automatically tags, renames (formats) and moves these files to your media server directory.<br>
Supports movie and tv show files and automatically recognises if a media file is a movie or an episode.<br>
Properly handles any mainstream scene file names, including multi-episodes.

###Usage
Run:

    watchdog.py
    
(I'm working on getting a '.exe' dist out soon.)<br>
Locate your source and destination directories through the GUI and add any renaming exception rules.<br>
Press 'Start'.

Or, manually run from the command line:

    renamer.py

It then loads your directories from the 'config.ini' file.

###Requirements
PyQt5
