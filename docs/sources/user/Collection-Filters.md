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
    paths: ['%%environ_systemroot%%\System32\winevt\Logs\SysEvent.evt']
    separator: '\'
conditions: [os_major_version < 6]
labels: [Logs]
supported_os: [Windows]
urls: ['https://forensics.wiki/windows_event_log_(evt)']
```

'WindowsEventLogSystem' refers to the path '%SystemRoot%\System32\winevt\Logs\SysEvent.evt'.

To use:

```bash
log2timeline.py --artifact-filters WindowsEventLogSystem --storage-file timeline.plaso source.raw
```

**Note that for convenience the Forensic Artifacts definition names can also
be stored in a file.**

## Using filter files

A YAML-based filter file can be used to describe the path of each file or
directory Plaso should include or exclude from parsing.

* Inclusion filters are applied before exclusion filters.
* Specifying the path of a directory will include or exclude its files and subdirectories.

Path filters are case sensitive when compared to a case sensitive file system
and case insensitive when compared to a case insensitive file system.

To use:

```bash
log2timeline.py --file-filter windows.yaml --storage-file timeline.plaso source.raw
```

**Note that filter files only support source-level filtering, meaning that
filters do not apply to archives or other composite files inside the source.**

### YAML-based filter file format

A path filter is defined as a set of attributes:

* "description"; optional description of the purpose of the path filter;
* "paths": one or more paths to filter defined as a regular expression;
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

**Note that if you use \ as a path segment separator it must be escaped as part
of the regular expression.**

## References

* [Forensic artifacts](https://github.com/ForensicArtifacts/artifacts)
* [Targeted Timeline Collection](http://blog.kiddaland.net/2013/02/targeted-timelines-part-i.html)

