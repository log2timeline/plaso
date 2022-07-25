# Using image_export.py

**PAGE WIP**

**image_export** is a command line tool to export file content from a storage media image or device based on various filter criteria, such as extension names, filter paths, file format signature identifiers, file creation date and time ranges, etc.

## Usage

To get a full list of parameters that can be passed to the tool use the ``-h`` or ``--help`` switch. The only required argument is ``IMAGE``, which should point to your source data.

```
image_export.py IMAGE
```

Command above will extract all unique allocated files and generate hashes.json file to ``export/`` directory, which is relative to the folder where you run ``image_export.py`` from. File ``hashes.json`` will contain list of unique hashes of extracted files. In case there are any duplicates, the file will contain paths to all duplicate files.

There are several ways to define how you want to limit the amount files to extract:
 + Based on path, filename or extension name
 + Based on time range
 + Based on format signature

### Format signatures
In order to extract files based on their signature, use flag ``--signatures``. To list all available file signatures run :

```
image_export.py --signatures list
```

To extract all files with Windows PE Binary signature use the command below:

```
image_export.py  --signatures exe_mz [IMAGE]
```

### Filename
You can filter the extracted files based on their filename. If you want extract all files with filename ``.bash_history`` use the command below:

```
image_export.py --names .bash_history [IMAGE]
```

Flag ``--names`` accept comma separated strings.

### Extension
You can extract files based on their extension. To extract all docx files run the command below:


```
image_export.py --extensions docx [IMAGE]
```

Flag ``--extensions`` accept comma separated strings.

### Time range
You can extract files, which timestamp falls into date time range provided in the command line parameters:

```
image_export.py --date-filter "crtime,2019-09-01,2019-09-30" [IMAGE]
```

Command above will extract all files created in September, 2019.


For more details on date time filtering run ``image_export.py -h``.

### Output folder
In order to specify custom output folder, where all the files will be extracted, provide ``-w`` flag:

```
image_export.py -w ~/image_export_output [IMAGE]
```

### Duplicate handling
By default image_export.py will not extract duplicate files, however paths to all duplicate files will be stored in hashes.json file. If you'd like to extract duplicate files add `` --include_duplicates`` flag.


### Collection filters
More details: [collection filters](Collection-Filters.md)


## Other options

Talk about:
```
--data
--vss_stores VSS_STORES
```
