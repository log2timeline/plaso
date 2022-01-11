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

[Forensic Artifacts](https://github.com/ForensicArtifacts/artifacts) definitions provide a more analyst centric approach to
collection filters.

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
urls: ['https://forensicswiki.xyz/wiki/index.php?title=Windows_Event_Log_(EVT)']
```

'WindowsEventLogSystem' refers to the path '%SystemRoot%\System32\winevt\Logs\SysEvent.evt'.

To use:

```bash
log2timeline.py --artifact-filters WindowsEventLogSystem --storage-file timeline.plaso source.raw
```

**Note that for convenience the Forensic Artifacts definition names can also
be stored in a file.**

## Using filter files

Due a limitations in the original text-based filter file format the YAML-based
filter format was introduced. We recommend using the YAML-based format.

A YAML-based filter can be used to describe the path of each file or
directory Plaso should include or exclude from parsing.

* Inclusion filters are applied before exclusion filters.
* Specifying the path of a directory will include or exclude its files and subdirectories.

Path filters are case sensitive when compared to a case sensitive file system
and case insensitive when compared to a case insensitive file system.

To use:

```bash
log2timeline.py --file-filter windows.yaml --storage-file timeline.plaso source.raw
```

### Text-based filter file format

A text-based filter can be used to describe the path of each file or
directory Plaso should include in parsing.

**Note that the text-based filter file does not support exclusion filters.
If you need this functionality use the YAML-based filter file instead.**

The text-based filter file itself contains a path filter per line or a line
starting `#` for comment.

```
# This is comment.
/ segment1 / segment2 / segment3 / ...
{systemroot} / segment2 / segment3 / ...
```

The path segment separator is a forward slash '/'.

A path segment can be defined as

* a string representing the exact name of the directory or file;
* a regular expression representing the name of the directory or file;
* a path expansion variable, denoted by a curly bracket, such as `{systemroot}`.

The path must be an absolute path, meaning that is should start with '/' or
with path expansion variable that Plaso was able to resolve during
preprocessing. Plaso will ignore path filters it does not consider valid.

For example:

```
{systemroot}/System32/config/.+[.]evt
/(Users|Documents And Settings)/.+/AppData/Roaming/Mozilla/Firefox/Profiles/.+/places.sqlite
```

The first line defines a path filter that uses the "systemroot" path expansion
variable that is discovered during preprocessing and denotes the Windows
SystemRoot folder. It will then process the directories and files with a name
that endswith ".evt".

The second line defines a path filter using both regular expressions and
strings to denote the location of Firefox history files.

### YAML-based filter file format

A YAML-based filter can be used to describe the path of each file or
directory Plaso should include or exclude from parsing.

Include filters have precedence above exclude filters.

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

