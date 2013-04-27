@echo off
del /q /s dist\plaso 2> NUL

rmdir /q /s dist\plaso 2> NUL

mkdir dist\plaso

xcopy /q /y ACKNOWLEDGEMENT dist\plaso
xcopy /q /y AUTHORS dist\plaso
xcopy /q /y LICENSE.TXT dist\plaso

xcopy /q /y /s dist\log2timeline\* dist\plaso
xcopy /q /y /s dist\pinfo\* dist\plaso
xcopy /q /y /s dist\pprof\* dist\plaso
xcopy /q /y /s dist\pshell\* dist\plaso
xcopy /q /y /s dist\psort\* dist\plaso
