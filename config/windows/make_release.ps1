# This scripts builds a release of plaso, in the form of plaso.zip
# It needs to be run from a freshly cloned plaso directory

$PyInstaller = "pyinstaller.exe"

If (-Not (Test-Path ${PyInstaller}))
{
	Write-Host "Missing PyInstaller." -foreground Red

	Exit 1
}

# Remove support for hachoir which is GPLv2 and cannot be distributed
# in binary form. Leave the formatter because it does not link in the
# hachoir code.
Get-Content ".\plaso\parsers\__init__.py" | %{$_ -replace "from plaso.parsers import hachoir", ""} | Set-Content ".\plaso\parsers\__init__.py.patched"
mv -Force .\plaso\parsers\__init__.py.patched .\plaso\parsers\__init__.py

Get-Content ".\plaso\parsers\presets.py" | %{$_ -replace "'hachoir', ", ""} | Set-Content ".\plaso\parsers\presets.py.patched"
mv -Force .\plaso\parsers\presets.py.patched .\plaso\parsers\presets.py

Get-Content ".\plaso\dependencies.py" | Select-String -pattern 'hachoir_' -notmatch | Set-Content ".\plaso\dependencies.py.patched"
mv -Force .\plaso\dependencies.py.patched .\plaso\dependencies.py

# Build the binaries for each tool

$Output = Invoke-Expression "${PyInstaller} --hidden-import artifacts --onedir tools\image_export.py"

If (${LastExitCode} -ne ${ExitSuccess})
{
	Write-Host ${Output} -foreground Red

	Exit 1
}
$Output = Invoke-Expression "${PyInstaller} --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\log2timeline.py"

If (${LastExitCode} -ne ${ExitSuccess})
{
	Write-Host ${Output} -foreground Red

	Exit 1
}
$Output = Invoke-Expression "${PyInstaller} --hidden-import artifacts --onedir tools\pinfo.py"

If (${LastExitCode} -ne ${ExitSuccess})
{
	Write-Host ${Output} -foreground Red

	Exit 1
}
$Output = Invoke-Expression "${PyInstaller} --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\psort.py"

If (${LastExitCode} -ne ${ExitSuccess})
{
	Write-Host ${Output} -foreground Red

	Exit 1
}
$Output = Invoke-Expression "${PyInstaller} --hidden-import artifacts --hidden-import requests --hidden-import dpkt --onedir tools\psteal.py"

# Clone l2tdevtools for the licenses
If (Test-Path "l2tdevtools")
{
	rm -Force -Recurse "l2tdevtools"
}
git.exe clone https://github.com/log2timeline/l2tdevtools

# Set up distribution package path
If (Test-Path "dist\plaso")
{
	rm -Force -Recurse "dist\plaso"
}
mkdir dist\plaso
mkdir dist\plaso\data
mkdir dist\plaso\licenses

xcopy /q /y ACKNOWLEDGEMENTS dist\plaso
xcopy /q /y AUTHORS dist\plaso
xcopy /q /y LICENSE dist\plaso
xcopy /q /y README dist\plaso

$dep = Get-Content l2tdevtools\data\presets.ini | Select-String -pattern '\[plaso\]' -context 0,1
Foreach ($d in $dep.context.DisplayPostContext.split(': ')[2].split(',')) {
	cp "l2tdevtools\data\licenses\LICENSE.$($d)" dist\plaso\licenses
}

rm -Force dist\plaso\licenses\LICENSE.hachoir-*
rm -Force dist\plaso\licenses\LICENSE.guppy
rm -Force dist\plaso\licenses\LICENSE.libexe
rm -Force dist\plaso\licenses\LICENSE.libwrc
rm -Force dist\plaso\licenses\LICENSE.mock
rm -Force dist\plaso\licenses\LICENSE.pbr

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
