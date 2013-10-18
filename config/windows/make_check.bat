@echo off
@rem Script to make sure the executables run after make_dist.bat.

dist\plaso\image_export.exe -h
dist\plaso\log2timeline.exe --info
dist\plaso\pinfo.exe
dist\plaso\plasm.exe -h
dist\plaso\pprof.exe
dist\plaso\preg.exe
dist\plaso\pshell.exe
dist\plaso\psort.exe

