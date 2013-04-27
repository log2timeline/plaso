@echo off
del /q /s build dist 2> NUL
rmdir /q /s build dist 2> NUL

set PYTHONPATH=C:\plaso-build\

C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir frontend\log2timeline.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir frontend\pinfo.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir frontend\pprof.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir frontend\pshell.py
C:\Python27\python.exe ..\pyinstaller\pyinstaller.py --onedir frontend\psort.py
