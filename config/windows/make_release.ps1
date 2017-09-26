# This scripts builds a release of plaso, in the form of plaso.zip
# It needs to be run from a freshly cloned plaso directory

# Remove support for hachoir which is GPLv2 and cannot be distributed
# # in binary form. Leave the formatter because it does not link in the
# # hachoir code.
Get-Content ".\plaso\parsers\__init__.py" | %{$_ -replace "from plaso.parsers import hachoir", ""} | Set-Content ".\plaso\parsers\__init__.py.patched"
mv -Force .\plaso\parsers\__init__.py.patched .\plaso\parsers\__init__.py

Get-Content ".\plaso\parsers\presets.py" | %{$_ -replace "'hachoir', ", ""} | Set-Content ".\plaso\parsers\presets.py.patched"
mv -Force .\plaso\parsers\presets.py.patched .\plaso\parsers\presets.py

Get-Content ".\plaso\dependencies.py" | Select-String -pattern 'hachoir_' -notmatch | Set-Content ".\plaso\dependencies.py.patched"
mv -Force .\plaso\dependencies.py.patched .\plaso\dependencies.py

# Copy all licenses in .\config\licenses\
mkdir .\config\licenses
git.exe clone https://github.com/log2timeline/l2tdevtools
$dep = Get-Content ..\l2tdevtools\data\presets.ini | Select-String -pattern '\[plaso\]' -context 0,1
Foreach ($d in $dep.context.DisplayPostContext.split(': ')[2].split(',')) {
    cp "..\l2tdevtools\data\licenses\LICENSE.$($d)" .\config\licenses\
}

rm -Force .\config\licenses\LICENSE.hachoir-*
rm -Force .\config\licenses\LICENSE.guppy
rm -Force .\config\licenses\LICENSE.libexe
rm -Force .\config\licenses\LICENSE.libwrc
rm -Force .\config\licenses\LICENSE.mock
rm -Force .\config\licenses\LICENSE.pbr

pyinstaller.exe --hidden-import artifacts --onedir tools\image_export.py
pyinstaller.exe --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\log2timeline.py
pyinstaller.exe --hidden-import artifacts --onedir tools\pinfo.py
pyinstaller.exe --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\psort.py
pyinstaller.exe --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\psteal.py

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
xcopy /q /y /s dist\psort\* dist\plaso
xcopy /q /y /s dist\psteal\* dist\plaso
xcopy /q /y data\* dist\plaso\data
xcopy /q /y C:\Python27\Lib\site-packages\zmq\libzmq.pyd dist\plaso

# Copy the artifacts yaml files
git.exe clone https://github.com/ForensicArtifacts/artifacts
mkdir dist\plaso\artifacts
xcopy /q /y artifacts\data\* dist\plaso\artifacts

# Makes plaso.zip
Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipfile]::CreateFromDirectory("$(pwd | % Path)\dist\plaso", "$(pwd| % Path)\plaso.zip")
