# Collection Filters

When you know beforehand which files are relevant for your analysis and which
files not, you can use collection filters to instruct Plaso to only collect
events from these files. This is also referred to as targeted collection.

Plaso supports the following methods of targeted collection:

* Using Forensic Artifacts definitions
* Using filter files

**Note that at the moment the different collection filters cannot be used
simultaneously.**

## Using Forensic Artifacts definitions

[Forensic Artifacts](https://github.com/ForensicArtifacts/artifacts) definitions
provide a more analyst centric approach to collection filters.

For example based on the definition:

```
name: WindowsEventLogSystem
doc: System Windows Event Log.
sources:
- type: FILE
  attributes:
    paths: ['%%environ_systemroot%%\System32\config\SysEvent.evt']
    separator: '\'
supported_os: [Windows]
urls: ['https://artifacts-kb.readthedocs.io/en/latest/sources/windows/EventLog.html']
```

'WindowsEventLogSystem' refers to the path '%SystemRoot%\System32\config\SysEvent.evt'.

To use:

```bash
log2timeline.py --artifact-filters WindowsEventLogSystem --storage-file timeline.plaso source.raw
```

Multiple names can be provided as a comma separated list.

**Note that for convenience the Forensic Artifacts definition names can also
be stored in a file, with one name per line, which is passed with
`--artifact_filters_file`. This option cannot be combined with
`--artifact-filters`.**

To use your own artifact definitions in addition to the ones that are shipped
with the artifacts project, pass a file or directory with definitions in the
[Forensic Artifacts format](https://artifacts.readthedocs.io/en/latest/sources/Format-specification.html)
with `--custom-artifact-definitions`. The names of these definitions can then
be used with `--artifact-filters`.

## Using filter files

A YAML-based filter file can be used to describe the path of each file or
directory Plaso should include or exclude from parsing.

* Inclusion filters are applied before exclusion filters.
* Specifying the path of a directory will include or exclude its files and subdirectories.

Path filters are case insensitive, regardless of whether the file system is
case sensitive.

To use:

```bash
log2timeline.py --file-filter windows.yaml --storage-file timeline.plaso source.raw
```

**Note that filter files only support source-level filtering, meaning that
filters do not apply to archives or other composite files inside the source.**

### YAML-based filter file format

A path filter is defined as a set of attributes:

* "description"; optional description of the purpose of the path filter;
* "paths": one or more absolute paths to filter defined as a regular expression;
* "path_separator"; optional path segment separator, which is '/' by default;
* "type"; required filter type either "include" or "exclude";

For example:

```
description: Windows Event Log files.
type: include
path_separator: '\'
paths:
- '%SystemRoot%\\System32\\config\\.+[.]evt'
---
description: Exclude Linux binaries.
type: exclude
paths:
- '/usr/bin'
```

The regular expression is applied per path segment, which means a regular
expression cannot match the path segment separator. For example
`/usr/(bin|sbin)/echo` matches both `/usr/bin/echo` and `/usr/sbin/echo`, and
`/usr/.+/echo` matches `/usr/bin/echo` but not `/usr/local/bin/echo`.

A path segment of the form `%Name%`, such as `%SystemRoot%`, is replaced by the
value of the corresponding Windows environment variable that was determined
during preprocessing. If the resulting path is not absolute, for example
because the environment variable could not be determined, the path is ignored
and a warning is logged.

**Note that if you use `\` as a path segment separator it must be escaped as part
of the regular expression of the paths attribute. Also make sure to escape any
special regular expression characters such as `$`.**

```
description: Exclude NTFS $BadClus metadata file.
type: exclude
path_separator: '\'
paths:
- '\\[$]BadClus'
```

## References

* [Forensic artifacts](https://github.com/ForensicArtifacts/artifacts)
* [Targeted Timeline Collection](http://blog.kiddaland.net/2013/02/targeted-timelines-part-i.html)

