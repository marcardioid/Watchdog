from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

setup(
    options = {'py2exe':
                   {'bundle_files': 1,
                    'dll_excludes': [
                        "MSVCP90.dll",
                        "MSWSOCK.dll",
                        "mswsock.dll",
                        "powrprof.dll",
                    ],
                    'includes': ['sip', 'PyQt5.QtNetwork']}
               },
    windows = [{'script': "watchdog.py", "icon_resources": [(1, "watchdog.ico")]}],
    zipfile = None,
    data_files = [('imageformats', [r'C:\Program Files\Python34\Lib\site-packages\PyQt5\plugins\imageformats\qico.dll'])],
)
