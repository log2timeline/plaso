@echo off
del /q /s dist\plaso 2> NUL

rmdir /q /s dist\plaso 2> NUL

mkdir dist\plaso
mkdir dist\plaso\data
mkdir dist\plaso\licenses

xcopy /q /y ACKNOWLEDGEMENTS dist\plaso
xcopy /q /y AUTHORS dist\plaso
xcopy /q /y LICENSE dist\plaso
xcopy /q /y README dist\plaso
xcopy /q /y config\licenses\* dist\plaso\licenses

xcopy /q /y /s dist\image_export\* dist\plaso
xcopy /q /y /s dist\log2timeline\* dist\plaso
xcopy /q /y /s dist\pinfo\* dist\plaso
xcopy /q /y /s dist\preg\* dist\plaso
xcopy /q /y /s dist\psort\* dist\plaso
xcopy /q /y data\* dist\plaso\data
