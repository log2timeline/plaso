# Scripts to build a onedir PyInstaller versions of the plaso tools.
# The tools are bundled into a single ZIP file.

# Note that Param must be called first.
# Usage: .\make_release.ps1 -Architecture win32
Param (
	[string]$Architecture = "amd64",
	[string]$PythonPath = ""
)

If ( -not $PythonPath )
{
	If ( $Architecture -eq "win32" )
	{
		# Note that the backtick here is used as escape character.
		$PythonPath = "C:\Python27` (x86)"
	}
	Else
	{
		$PythonPath = "C:\Python27"
	}
}

Try
{
	# -ErrorAction Stop causes Get-Command to raise a non-terminating
	# exception. A non-terminating exception will not be caught by
	# try-catch.
	$PyInstaller = (Get-Command "pyinstaller.exe" -ErrorAction Stop).Path
	$Python = ""
}
Catch
{
	$PyInstaller = "pyinstaller.exe"
}

If (-Not (Test-Path $PyInstaller))
{
	$PyInstaller = "..\pyinstaller\pyinstaller.py"

	If (-Not (Test-Path $PyInstaller))
	{
	    Write-Host "Missing PyInstaller." -foreground Red

	    Exit 1
	}
	$Python = "${PythonPath}\python.exe"

	If (-Not (Test-Path $Python))
	{
	    Write-Host "Missing Python: ${Python}." -foreground Red

	    Exit 1
	}
}

$Version = & Invoke-Expression -Command "git describe --tags --abbrev=0"

# Build the binaries for each tool
If (Test-Path "dist")
{
    rm -Force -Recurse "dist"
}

$Arguments = "--hidden-import artifacts --onedir tools\image_export.py"

If ( $Python -ne "" )
{
	Invoke-Expression -Command "& '${Python}' ${PyInstaller} ${Arguments}"
}
Else
{
	Invoke-Expression -Command "${PyInstaller} ${Arguments}"
}
If ( $LastExitCode -ne 0 ) {
    Write-Host "Error running PyInstaller for tools\image_export.py." -foreground Red
    Exit 1
}

$Arguments = "--hidden-import artifacts --hidden-import future --hidden-import requests --onedir tools\log2timeline.py"

If ( $Python -ne "" )
{
	Invoke-Expression -Command "& '${Python}' ${PyInstaller} ${Arguments}"
}
Else
{
	Invoke-Expression -Command "${PyInstaller} ${Arguments}"
}
If ( $LastExitCode -ne 0 ) {
    Write-Host "Error running PyInstaller for tools\log2timeline.py." -foreground Red
    Exit 1
}

$Arguments = "--hidden-import artifacts --onedir tools\pinfo.py"

If ( $Python -ne "" )
{
	Invoke-Expression -Command "& '${Python}' ${PyInstaller} ${Arguments}"
}
Else
{
	Invoke-Expression -Command "${PyInstaller} ${Arguments}"
}
If ( $LastExitCode -ne 0 ) {
    Write-Host "Error running PyInstaller for tools\pinfo.py." -foreground Red
    Exit 1
}

$Arguments = "--hidden-import artifacts --hidden-import requests --onedir tools\psort.py"

If ( $Python -ne "" )
{
	Invoke-Expression -Command "& '${Python}' ${PyInstaller} ${Arguments}"
}
Else
{
	Invoke-Expression -Command "${PyInstaller} ${Arguments}"
}
If ( $LastExitCode -ne 0 ) {
    Write-Host "Error running PyInstaller for tools\psort.py." -foreground Red
    Exit 1
}

$Arguments = "--hidden-import artifacts --hidden-import future --hidden-import requests --onedir tools\psteal.py"

If ( $Python -ne "" )
{
	Invoke-Expression -Command "& '${Python}' ${PyInstaller} ${Arguments}"
}
Else
{
	Invoke-Expression -Command "${PyInstaller} ${Arguments}"
}
If ( $LastExitCode -ne 0 ) {
    Write-Host "Error running PyInstaller for tools\psteal.py." -foreground Red
    Exit 1
}

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

xcopy /q /y /s dist\image_export\* dist\plaso
xcopy /q /y /s dist\log2timeline\* dist\plaso
xcopy /q /y /s dist\pinfo\* dist\plaso
xcopy /q /y /s dist\psort\* dist\plaso
xcopy /q /y /s dist\psteal\* dist\plaso
xcopy /q /y data\* dist\plaso\data
xcopy /q /y "${PythonPath}\Lib\site-packages\zmq\libzmq.pyd" dist\plaso

# Copy the license files of the dependencies
git.exe clone https://github.com/log2timeline/l2tdevtools dist\l2tdevtools

$dep = Get-Content dist\l2tdevtools\data\presets.ini | Select-String -pattern '\[plaso\]' -context 0,1
Foreach ($d in $dep.context.DisplayPostContext.split(': ')[2].split(',')) {
    cp "dist\l2tdevtools\data\licenses\LICENSE.$($d)" dist\plaso\licenses
}

# Remove debug, test and yet unused dependencies.
rm -Force dist\plaso\licenses\LICENSE.guppy
rm -Force dist\plaso\licenses\LICENSE.libexe
rm -Force dist\plaso\licenses\LICENSE.libwrc
rm -Force dist\plaso\licenses\LICENSE.mock
rm -Force dist\plaso\licenses\LICENSE.pbr

# Copy the artifacts yaml files
git.exe clone https://github.com/ForensicArtifacts/artifacts.git dist\artifacts
cd dist\artifacts
$latest_tag=git.exe describe --tags $(git.exe rev-list --tags --max-count=1)
git.exe checkout $latest_tag
cd ..\..
mkdir dist\plaso\artifacts
xcopy /q /y dist\artifacts\data\*.yaml dist\plaso\artifacts

# Copy the dfVFS yaml (dtFabric definition) files
git.exe clone https://github.com/log2timeline/dfvfs.git dist\dfvfs
cd dist\dfvfs
$latest_tag=git.exe describe --tags $(git.exe rev-list --tags --max-count=1)
git.exe checkout $latest_tag
cd ..\..
mkdir dist\plaso\dfvfs\lib
xcopy /q /y dist\dfvfs\dfvfs\lib\*.yaml dist\plaso\dfvfs\lib

# Copy the dfWinReg yaml (dtFabric definition) files
git.exe clone https://github.com/log2timeline/dfwinreg.git dist\dfwinreg
cd dist\dfwinreg
$latest_tag=git.exe describe --tags $(git.exe rev-list --tags --max-count=1)
git.exe checkout $latest_tag
cd ..\..
mkdir dist\plaso\dfwinreg
xcopy /q /y dist\dfwinreg\dfwinreg\*.yaml dist\plaso\dfwinreg

# Copy the plaso yaml (dtFabric definition) files
mkdir dist\plaso\plaso\parsers
mkdir dist\plaso\plaso\parsers\esedb_plugins
mkdir dist\plaso\plaso\parsers\olecf_plugins
mkdir dist\plaso\plaso\parsers\plist_plugins
mkdir dist\plaso\plaso\parsers\winreg_plugins
xcopy /q /y plaso\parsers\*.yaml dist\plaso\plaso\parsers
xcopy /q /y plaso\parsers\esedb_plugins\*.yaml dist\plaso\plaso\parsers\esedb_plugins
xcopy /q /y plaso\parsers\olecf_plugins\*.yaml dist\plaso\plaso\parsers\olecf_plugins
xcopy /q /y plaso\parsers\plist_plugins\*.yaml dist\plaso\plaso\parsers\plist_plugins
xcopy /q /y plaso\parsers\winreg_plugins\*.yaml dist\plaso\plaso\parsers\winreg_plugins

# Makes plaso-<version>-<architecture>.zip
Add-Type -assembly "system.io.compression.filesystem"
[io.compression.zipfile]::CreateFromDirectory("$(pwd | % Path)\dist\plaso", "$(pwd| % Path)\plaso-${Version}-${Architecture}.zip")
