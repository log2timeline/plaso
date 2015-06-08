@echo off
del /q /s build dist 2> NUL
rmdir /q /s build dist 2> NUL

set PYTHONPATH=.

C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir tools\image_export.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir tools\log2timeline.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir tools\pinfo.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir tools\preg.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir tools\psort.py

set PYTHONPATH=
