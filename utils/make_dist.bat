@echo off
del /q /s dist\plaso

rmdir /q /s dist\plaso

mkdir dist\plaso

xcopy /q /y /s dist\log2timeline\* dist\plaso
xcopy /q /y /s dist\plaso_console\* dist\plaso
xcopy /q /y /s dist\plaso_information\* dist\plaso
xcopy /q /y /s dist\pprof\* dist\plaso
xcopy /q /y /s dist\psort\* dist\plaso
