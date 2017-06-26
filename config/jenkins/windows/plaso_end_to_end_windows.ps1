# Script to run automated end-to-end tests on Windows platforms
#
# This script requires four arguments to run:
#   $config_file : the path to the test configuration INI file to use
#   $config_bucket_baseurl : the base URL for the Cloud bucket
#       where test configuration files are stored.
#   $evidence_bucket_baseurl : the base URL for the Cloud bucket
#       where evidence/source files are stored.
#   $results_bucket_baseurl : the base URL for the Cloud bucket
#       where the test results should be uploaded.
#
# Example:
#   powershell.exe plaso_end_to_end_windows.ps1 `
#     -config_file studentpc1-noprofile.ini `
#     -config_bucket_baseurl gs://bucket1 `
#     -evidence_bucket_baseurl gs://bucket2 `
#     -results_bucket_baseurl gs://bucket3

param (
   [Parameter(Mandatory=$true)]
   [string]$config_file,
   [Parameter(Mandatory=$true)]
   [string]$config_bucket_baseurl,
   [Parameter(Mandatory=$true)]
   [string]$evidence_bucket_baseurl,
   [Parameter(Mandatory=$true)]
   [string]$results_bucket_baseurl
)

# Some hardcoded values
$gsutilexec = 'gsutil'
$data_directory = 'C:\data\'
$plaso_tools_directory = '.\tools'

# Some helper functions
function Exists-Command {
    <#
    .SYNOPSIS
      Returns True if a command exists.

    .PARAMETER Name
      The command to check.

    .OUTPUTS
      True if the command exists.
    #>

    param (
        [string]$Name
    )

    return ((Get-Command $Name -errorAction SilentlyContinue) -ne $null)
}

Function Get-IniContent {
    <#
    .SYNOPSIS
        Returns the content of a well formed INI file as a hashmap.

    .PARAMETER IniFile
        The path to the INI file.

    .OUTPUTS
      A hashmap reflecting the content of the INI file.
    #>

    Param(
        [string]$IniFile
    )
        $hashmap = @{}
        switch -regex -file $IniFile
        {
            "^(;.*)$"
            {
                # This is a comment, do nothing.
            }
            "^\[(.+)\]$"
            {
                $current_section = $matches[1]
                $hashmap[$current_section] = @{}
            }
            "(.+?)\s*=\s*(.*)" # key=value
            {
                $key = $matches[1]
                $value = $matches[2]
                $hashmap[$current_section][$key] = $value
            }
        }
        Return $hashmap
}

# Checking variables are set properly

if ( ! $config_file ) {
    throw 'Please specify the name of the INI configuration file'
}

$tests_configuration = Get-IniContent $config_file
$tests_set_name = $tests_configuration.Keys[0]
$evidence_filename = $tests_configuration["$tests_set_name"]["source"]

$results_directory = "plaso_end_to_end_windows_$tests_set_name"

$evidence_path = "$($data_directory)\$($evidence_filename)"
$config_storage_url = "$($config_bucket_baseurl)/$($config_file)"
$evidence_storage_url = "$($evidence_bucket_baseurl)/$($evidence_filename)"

$job = If ($env:JOB_NAME) {$env:JOB_NAME} Else {'test-job'}
$build = If ($env:BUILD_NUMBER) {$env:BUILD_NUMBER} Else {'test-buildnum'}

$pythonexec = 'C:\Python27\python.exe'
if (! $(Exists-Command $pythonexec)) {
    $pythonexec = 'C:\Program Files\Python27\python.exe'
    if (! $(Exists-Command $pythonexec)) {
        throw "Unable to find Python executable $($pythonexec)"
    }
}

if (! $(Exists-Command $gsutilexec)) {
   throw "Unable to find GSutil executable $($gsutilexec)"
}

if (!(Test-Path -Path $plaso_tools_directory)) {
    throw "Unable to find tools directory $($plaso_tools_directory)"
}

if (Test-Path -Path $results_directory) {
    Remove-Item -Recurse -Force $results_directory
}
New-Item -ItemType directory -Path $results_directory

if (!(Test-Path -Path $data_directory)) {
    New-Item -ItemType directory -Path $data_directory
}

if (!(Test-Path -Path $evidence_path)) {
    Write-Host "Copying $($evidence_storage_url) to $($evidence_path)"
    & $gsutilexec cp $evidence_storage_url $evidence_path
}

if (!(Test-Path -Path $config_file)) {
    Write-Host "Copying $($config_storage_url) to $($config_file)"
    & $gsutilexec cp $config_storage_url $config_file
}

# Run test
$env:PYTHONPATH = '.'
Write-Host "Running $($pythonexec) .\tests\end-to-end.py --debug --config " +
  "$($config_file) --sources-directory $($data_directory) --tools-directory "+
  "$($plaso_tools_directory) --results-directory $($results_directory)"
& $pythonexec .\tests\end-to-end.py --debug --config $config_file `
  --sources-directory $data_directory --tools-directory $plaso_tools_directory `
  --results-directory $results_directory 2>&1

if ($LastExitCode -ne 0) {
    throw "Error running the end to end test"
}

# Export test results to storage bucket
Write-Host "Running $($gsutilexec) cp $($results_directory) "+
  "$($results_bucket_baseurl)/$($results_directory)/$($job)/$($build)"
& $gsutilexec cp -r $results_directory `
  "$results_bucket_baseurl/$results_directory/$job/$build"

Write-Host "All done!"
