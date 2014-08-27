@echo off
del /q /s build dist 2> NUL
rmdir /q /s build dist 2> NUL

set PYTHONPATH=.

C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\image_export.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\log2timeline.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\pinfo.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\plasm.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\pprof.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\preg.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\pshell.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir plaso\frontend\psort.py

set PYTHONPATH=
