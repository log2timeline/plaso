# Using image_export.py

**image_export** is a command line tool to export file content from a storage media image, device or directory based on various filter criteria, such as file names, extension names, filter paths, Forensic Artifacts definitions, file format signature identifiers, date and time ranges, etc.

## Usage

To get a full list of parameters that can be passed to the tool use the ``-h`` or ``--help`` switch. The only required argument is ``IMAGE``, which should point to your source data. The source must be a storage media image, a storage media device or a directory; a single file is not supported.

```
image_export.py IMAGE
```

Command above will extract all unique allocated files and generate a ``hashes.json`` file in the ``export/`` directory, which is relative to the folder where you run ``image_export.py`` from. File ``hashes.json`` will contain a list of the SHA-256 hashes of the extracted files. In case there are any duplicates, the file will contain paths to all duplicate files.

For example, running ``image_export.py`` on ``test_data/image.qcow2`` from the Plaso source creates the following files in the export directory:

```
./a_directory/a_file
./a_directory/another_file
./hashes.json
./passwords.txt
```

Where ``hashes.json`` contains:

```
[{"sha256": "02a2a6af2f1ecf4720d7d49d640f0d0a269a7ec733e41973bdd34f09dad0e252", "paths": ["passwords.txt"]}, {"sha256": "c7fbc0e821c0871805a99584c6a384533909f68a6bbe9a2a687d28d9f3b10c16", "paths": ["a_directory/another_file"]}, {"sha256": "4a49638d0e1055fd9e4c17fef7fdf4d6ccf892b6d9c2f64164203c4bfb0ec92d", "paths": ["a_directory/a_file"]}]
```

There are several ways to define how you want to limit the amount of files to extract:
 + Based on path, filename or extension name
 + Based on time range
 + Based on format signature
 + Based on Forensic Artifacts definitions or a filter file

The ``--names``, ``--extensions``, ``--signatures`` and ``--date-filter`` filters are combined: a file is exported when it matches any one of them. For example ``--names passwords.txt --extensions docx`` exports both files named ``passwords.txt`` and files with the ``docx`` extension. Forensic Artifacts definitions and filter files limit which paths are considered in the first place.

### Format signatures
In order to extract files based on their signature, use flag ``--signatures``. To list all available file signatures run:

```
image_export.py --signatures list
```

To extract all files with Windows PE Binary signature use the command below:

```
image_export.py --signatures exe_mz [IMAGE]
```

The signatures are read from ``signatures.conf`` in the data location. If the data location cannot be determined automatically, specify it with ``--data PATH``.

### Filename
You can filter the extracted files based on their filename. If you want extract all files with filename ``.bash_history`` use the command below:

```
image_export.py --names .bash_history [IMAGE]
```

Flag ``--names`` accept comma separated strings. File names are compared case insensitive.

### Extension
You can extract files based on their extension. To extract all docx files run the command below:


```
image_export.py --extensions docx [IMAGE]
```

Flag ``--extensions`` accept comma separated strings.

### Time range
You can extract files, which timestamp falls into date time range provided in the command line parameters:

```
image_export.py --date-filter "crtime,2019-09-01,2019-10-01" [IMAGE]
```

Command above will extract all files created in September, 2019 (up to and including 2019-10-01 00:00:00). The filter is formatted as ``TIME_VALUE,START,END``, where ``TIME_VALUE`` is one of: ``atime``, ``bkup``, ``ctime``, ``crtime``, ``dtime`` or ``mtime``. A date and time without a time of day, such as ``2019-10-01``, means midnight (00:00:00) UTC at the start of that day. Either ``START`` or ``END`` can be left empty for an open ended range, for example ``"mtime,2019-09-01,"``. The ``--date-filter`` option can be repeated, for example once for ``atime`` and once for ``crtime``.

**Note that a file that does not have the selected timestamp is not excluded by that date filter.** For example ext2 does not store a creation time, so a ``crtime`` date filter will export all files from an ext2 file system. On ``test_data/image.qcow2`` a ``crtime`` filter for 1990 exports all the files:

```
image_export.py --date-filter "crtime,1990-01-01,1990-12-31" test_data/image.qcow2
```

```
./a_directory/a_file
./a_directory/another_file
./hashes.json
./passwords.txt
```

While a ``mtime`` filter for the same range exports none:

```
image_export.py --date-filter "mtime,1990-01-01,1990-12-31" test_data/image.qcow2
```

```
./hashes.json
```

For more details on date time filtering run ``image_export.py -h``.

### Forensic Artifacts definitions
You can extract the files described by [Forensic Artifacts](https://github.com/ForensicArtifacts/artifacts) definitions, by name:

```
image_export.py --artifact_filters WindowsEventLogSystem [IMAGE]
```

Flag ``--artifact_filters`` accepts comma separated artifact definition names. The names can also be stored in a file, with one name per line, and passed with ``--artifact_filters_file PATH``. Custom artifact definitions can be added with ``--custom_artifact_definitions PATH``.

Add ``--enable_artifacts_map`` to write an ``artifacts_map.json`` file to the export directory, which maps the extracted files and directories to the artifact definitions that matched them.

More details: [collection filters](Collection-Filters.md)

### Filter files
You can also extract files based on a YAML-based filter file, with the ``-f`` or ``--file-filter`` flag:

```
image_export.py -f filter.yaml [IMAGE]
```

The paths in the filter file are matched against the paths of the files to export, and can contain regular expressions. To export the files in a directory, use a regular expression that matches the files in that directory; the path of the directory alone does not export its files. For example the filter file:

```
description: Include the files in a_directory.
type: include
paths:
- '/a_directory/.+_file'
```

exports the following files from ``test_data/image.qcow2``:

```
./a_directory/a_file
./a_directory/another_file
./hashes.json
```

More details on the filter file format: [collection filters](Collection-Filters.md)

### Output folder
In order to specify custom output folder, where all the files will be extracted, provide ``-w`` flag:

```
image_export.py -w ~/image_export_output [IMAGE]
```

The output folder must not be a symbolic link.

### Duplicate handling
By default image_export.py will not extract duplicate files, however paths to all duplicate files will be stored in hashes.json file. If you'd like to extract duplicate files add ``--include_duplicates`` flag.

If you do not want the ``hashes.json`` file to be generated add ``--no_hashes`` flag.

## Partitions, volumes, VSS and encrypted volumes

Like log2timeline.py, image_export.py scans the source and asks the user which partitions, volumes and Volume Shadow Snapshots (VSS) to process, and for credentials to unlock encrypted volumes. To prevent these prompts use:

* **--partitions PARTITIONS**: the partitions to process, for example `--partitions 2` or `--partitions all`.
* **--volumes VOLUMES**: the volumes to process, for example `--volumes all`.
* **--vss_stores VSS_STORES**: the VSS stores to process, for example `--vss_stores all`, `--vss_stores 1..3` or `--vss_stores none`. Use **--vss_only** to only process the VSS stores and not the current volume.
* **--credential TYPE:DATA**: the credential to unlock an encrypted volume, for example `--credential password:BDE-test`. Note that credentials passed via command line arguments can end up in logs.
* **-u** or **--unattended**: image_export.py will terminate with an error instead of prompting the user.

More details: [Using log2timeline](Using-log2timeline.md)
