# Script to set up tests on AppVeyor Windows.

$Dependencies = "PyYAML XlsxWriter artifacts bencode certifi cffi chardet cryptography dateutil defusedxml dfdatetime dfvfs dfwinreg dtfabric fakeredis future idna libbde libcreg libesedb libevt libevtx libewf libfsapfs libfsext libfshfs libfsntfs libfsxfs libfvde libfwnt libfwsi liblnk libluksde libmodi libmsiecf libolecf libphdi libqcow libregf libscca libsigscan libsmdev libsmraw libvhdi libvmdk libvsgpt libvshadow libvslvm lz4 mock opensearch-py pbr pefile psutil pyparsing pytsk3 pytz pyzmq redis requests six sortedcontainers urllib3 xattr yara-python"
$Dependencies = ${Dependencies} -split " "

$Output = Invoke-Expression -Command "git clone https://github.com/log2timeline/l2tdevtools.git ..\l2tdevtools 2>&1"
Write-Host (${Output} | Out-String)

If ($env:APPVEYOR_REPO_BRANCH -eq "main")
{
	$Track = "stable"
}
Else
{
	$Track = $env:APPVEYOR_REPO_BRANCH
}
New-Item -ItemType "directory" -Name "dependencies"

$env:PYTHONPATH = "..\l2tdevtools"

$Output = Invoke-Expression -Command "& '${env:PYTHON}\python.exe' ..\l2tdevtools\tools\update.py --download-directory dependencies --machine-type ${env:MACHINE_TYPE} --msi-targetdir ${env:PYTHON} --track ${env:L2TBINARIES_TRACK} ${Dependencies} 2>&1"
Write-Host (${Output} | Out-String)

