# Avoid re-running
if (Test-Path -Path $data_directory) {
    Write-Host 'Tools already present, exiting startup script.'
    exit
}

## Set up default URLs and Paths
$install_log_path = "$($data_directory)\provision.log"
$jenkins_slave_path = "$($jenkins_home_directory)\slave.jar"
$vc_for_python_url = 'https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi'
$vc_for_python_path = "$($data_directory)\VCForPython27.msi"
$vs_registry_key_path = 'HKLM:\Software\Wow6432Node\Microsoft\VisualStudio\9.0\Setup\VC'
$vs_registry_key_value = "C:\Users\$($username)\AppData\Local\Programs\Common\Microsoft\Visual C++ for Python\9.0"

mkdir $data_directory

## Download & install Visual Studio for Python
echo "Downloading $($vc_for_python_url) to $($vc_for_python_path)" | Tee-Object -Append -FilePath $install_log_path
(New-Object System.Net.WebClient).DownloadFile($vc_for_python_url, $vc_for_python_path)
echo 'Download complete, now installing' | Tee-Object -Append -FilePath $install_log_path
$msiexec_arguments=@"
/i $($vc_for_python_path) ROOT="$($vs_registry_key_value)" /qn /L*+ $($install_log_path)
"@
Start-Process msiexec.exe -Wait -ArgumentList $msiexec_arguments
echo "Adding registry key $($vs_registry_key_path)\productdir with value $($vs_registry_key_value)" | Tee-Object -Append -FilePath $install_log_path
New-Item $vs_registry_key_path -Force | New-ItemProperty -Name productdir -Value $vs_registry_key_value -Force
echo 'Installing Microsoft Visual C++ Compiler for Python 2.7... done!' | Tee-Object -Append -FilePath $install_log_path

## Download & install Chocolatey
echo 'Installing Chocolatey' | Tee-Object -Append -FilePath $install_log_path
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
#
## Set up SSHd
$user_dirs = Get-ChildItem "C:\Users\$($username)*"
$user_dir = $user_dirs[0].FullName
$ssh_user_directory = "$($user_dir)\.ssh"
$authorized_keys_path = "$($ssh_user_directory)\authorized_keys"
mkdir $ssh_user_directory | Tee-Object -Append -FilePath $install_log_path

echo 'Installing SSHd' | Tee-Object -Append -FilePath $install_log_path
Choco install openssh -y --force --params '"/SSHServerFeature"' | Tee-Object -Append -FilePath $install_log_path
echo "Write public key to $($authorized_keys_path) file" | Tee-Object -Append -FilePath $install_log_path
Set-content -Path $authorized_keys_path -Encoding ASCII -Value $pub_key_content

echo 'Give read access to SSHd' | Tee-Object -Append -FilePath $install_log_path
$Acl = Get-Acl $authorized_keys_path
$Ar = New-Object system.security.accesscontrol.filesystemaccessrule("NT SERVICE\sshd","Read","Allow")
$Acl.SetAccessRule($Ar)
Set-Acl $authorized_keys_path $Acl

echo "Remove extra permissions on $($authorized_keys_path)" | Tee-Object -Append -FilePath $install_log_path
.\icacls.exe $($authorized_keys_path) /inheritance:d
.\icacls.exe $($authorized_keys_path) /remove Everyone
.\icacls.exe $($authorized_keys_path) /remove BUILTIN\Users

echo "New ACLs for $($authorized_keys_path):" | Tee-Object -Append -FilePath $install_log_path
Get-Acl $authorized_keys_path | Tee-Object -Append -FilePath $install_log_path

## Install plaso dependencies
Choco install patch -y | Tee-Object -Append -FilePath $install_log_path # Used when building plaso dependencies
Choco install jre8 -y | Tee-Object -Append -FilePath $install_log_path # Needed for jenkins client
Choco install git -y --params '"/GitAndUnixToolsOnPath"' | Out-Null #Tee-Object -Append -FilePath $install_log_path
Choco install python2 -y | Tee-Object -Append -FilePath $install_log_path
# Pip package is broken as per 2017-07-14
Choco install pip -y --allow-empty-checksums | Tee-Object -Append -FilePath $install_log_path
Choco install vcredist2010 -y | Tee-Object -Append -FilePath $install_log_path

c:\python27\scripts\pip.exe install wmi | Tee-Object -Append -FilePath $install_log_path
c:\python27\scripts\pip.exe install pypiwin32 | Tee-Object -Append -FilePath $install_log_path
c:\python27\scripts\pip.exe install requests | Tee-Object -Append -FilePath $install_log_path
c:\python27\scripts\pip.exe install pyinstaller | Tee-Object -Append -FilePath $install_log_path

echo 'Downloading Jenkins client' | Tee-Object -Append -FilePath $install_log_path
mkdir $jenkins_home_directory
(New-Object System.Net.WebClient).DownloadFile($jenkins_slave_url, $jenkins_slave_path)

# Disable stupid UAC
New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"  -Name EnableInstallerDetection -Value 0 -Force
# This needs a reboot to be applied

Restart-Computer
