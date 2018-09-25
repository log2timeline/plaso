# Using image_export.py

**PAGE WIP**

**image_export** is a command line tool to export file content from a storage media image or device based on various filter criteria, such as extension names, filter paths, file format signature identifiers, file creation date and time ranges, etc.

## Usage

To get a full list of parameters that can be passed to the tool use the ``-h`` or ``--help`` switch.

There are several ways to define how you want to find the files to extract:
 + Based on path, filename or extension name
 + Based on time range
 + Based on format signature

### Path, filename or extension

discuss here:

```
--names NAMES
```

```
-f FILE_FILTER
```
[collection filters](Collection-Filters.md)

```
-x EXTENSIONS, --extensions EXTENSIONS
```

## Time range

--date-filter TYPE_START_END, --date_filter TYPE_START_END

## Format signature

 --signatures IDENTIFIERS

## Other options

Talk about:
--data 
-w PATH

--include_duplicates

--no_vss
--vss_stores VSS_STORES
