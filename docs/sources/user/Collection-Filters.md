**This page is still being worked on.**

*n.b. collections filters will soon be replaced by [artifacts](https://github.com/ForensicArtifacts/artifacts)*

The idea behind collection filters is simple. If the user of the tool knows beforehand where files of potential interest lie there is no need to go through each and ever file in the filesystem. A filter file can be created that describes the location of each file the collector should look for to include in the parsing and no other file should be included.

The filter file itself is a simple entry per line where each line in the filter file describes a single location to include. The format is essentially:

FIELD 1 | SEPARATOR | FIELD 2 | SEPARATOR | FIELD 3 | ...

The separator is a forward slash '/' and each field represents a directory up until the last one, which denotes the files to include. A field can be one of the following three options:

 + A string representing the exact directory name, case insensitive.
 + A regular expression denoting the name of the directory or file.
 + A name of an attribute collected during the preprocessing stage, denoted by a curly bracket {attribute_name}.

This can lead to a line similar to this:

```
{sysregistry}/.+evt
```

Or

```
/(Users|Documents And Settings)/.+/AppData/Roaming/Mozilla/Firefox/Profiles/.+/places.sqlite
```

The first filter line uses an attribute called "*sysregistry*" that is discovered during the preprocessing stage and denotes the folder location that stores the system registry files. It will then include all files that end with the three letters "*evt*" in the collection. 

The second line however uses both regular expressions and regular strings to denote the location of Firefox history files.

Each one of these files may produce more than one directory, and each directory can contain more than a single file, resulting in a single line in the filter file perhaps discovering several files in different directories on the system.

These files can be used to limit the collection of data from a machine and target the parsing, thus both reducing the amount of irrelevant events in the timeline and reduce the time it takes to parse an image using the tool.

An important caveat is that collection filters do not offer the option of blacklisting, that is to say every file in a folder except files that match pattern *foo*. Another important caveat is that there is no support for recursion, which means that something like ```/Users/.+/AppData/**`` or something like that would not search the AppData folder and every subfolder under that. These feature requests are being tracked [here](https://github.com/log2timeline/plaso/issues/103)
