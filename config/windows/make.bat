@echo off
del /q /s build dist 2> NUL
rmdir /q /s build dist 2> NUL

set PYTHONPATH=.

C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --hidden-import artifacts --onedir tools\image_export.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\log2timeline.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --hidden-import artifacts --onedir tools\pinfo.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --hidden-import artifacts --hidden-import IPython --onedir tools\preg.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\psort.py

set PYTHONPATH=
