# How to write a parser or (parser) plugin

## Introduction

This page is intended to give you an introduction into developing a parser for
Plaso.

* A step-by-step example is provided to create a simple binary parser for the Safari Cookies.binarycookies file.
* At bottom are some common troubleshooting tips that others have run into before you.

This page assumes you have at least a basic understanding of programming in
Python and use of git.

### Terminology

* event; a subclass of [EventObject](../api/plaso.containers.html#plaso.containers.events.EventObject) which represents [an event](../user/Scribbles-about-events.html#what-is-an-event)
* event data; a subclass of [EventData](../api/plaso.containers.html#plaso.containers.events.EventData) which represents data related to the event.
* event data stream; a subclass of [EventDataStream](../api/plaso.containers.html#plaso.containers.events.EventDataStream) which represents the data stream which the event data originated from.
* message formatter; a configuration driven subsystem of Plaso that generates a human readable message of the event data.
* timeliner; a configuration driven subsystem of Plaso that generates events from event data.
* parser; a subclass of [FileObjectParser](../api/plaso.parsers.html#plaso.parsers.interface.FileObjectParser) that extracts event data from a file.
* parser plugin; an extension of existing parser, such as the SQLite parser, that extracts event data from a file.

## Before you start

Before you can write a binary file parser you will need to have a good
understanding of the data format. Several things can help here:

* having a diverse set of test data, preferable test data that is reproducible. Examples of how to create reproducible test data can be found [here](https://github.com/dfirlabs)
* having format specifications

### Parser or (parser) plugin

Before starting work on a parser, check if Plaso already has a parser that
handles the underlying data format. Plaso currently supports (parser) plugins
for the following file formats:

* Bencode
* Compound ZIP archives
* Web Browser Cookies
* Extensible Storage Engine (ESE) databases
* Single-line JSON-L log files
* OLE Compound files
* Plist files
* [SQLite database files](How-to-write-a-SQLite-plugin.md)
* Text-based log files
* Windows Registry files (CREG and REGF)

If the data format you are trying to parse is in one of these formats, you
will need to write a (parser) plugin rather than a parser.

## Writing a parser

For our example, the Safari Cookies.binarycookies file has its own unique data
format, hence we need to create a separate parser.

A description of the Safari Cookies.binarycookies format can be found
[here](https://github.com/libyal/dtformats/blob/main/documentation/Safari%20Cookies.asciidoc).

### Test data

First we make a representative test file and add it to the `test_data/`
directory, in our example:

```
test_data/Cookies.binarycookies
```

**Make sure that the test file does not contain sensitive or copyrighted
material.**

### The parser

Next create the parser and add it to the `plaso/parsers/` directory.

```
plaso/parsers/safari_cookies.py
```

~~~~python
"""Parser for Safari Binary Cookie files."""

import os

from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class BinaryCookieParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
    """Parser for Safari Binary Cookie files."""

    NAME = "binary_cookies"
    DATA_FORMAT = "Safari Binary Cookie file"

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "safari_cookies.yaml")

    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification for parser selection.

        Returns:
          FormatSpecification: format specification.
        """
        format_specification = specification.FormatSpecification(cls.NAME)
        format_specification.AddNewSignature(b"cook\x00", offset=0)
        return format_specification

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a Safari binary cookie file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object to be parsed.

        Raises:
          WrongParser: when the file cannot be parsed, this will signal
              the event extractor to apply other parsers.
        """
        file_header_map = self._GetDataTypeMap("binarycookies_file_header")

        try:
            file_header, file_header_data_size = self._ReadStructureFromFileObject(
                file_object, 0, file_header_map
            )
        except (ValueError, errors.ParseError) as exception:
            raise errors.WrongParser(
                f"Unable to read file header with error: {exception!s}."
            )

        ...


manager.ParsersManager.RegisterParser(BinaryCookieParser)
~~~~

`manager.ParsersManager.RegisterParser(BinaryCookieParser)` is used to
register the parser with the unique name `binary_cookies`.

`GetFormatSpecification` defines the signature of the format, which Plaso
uses to determine which parsers to apply to a file. A parser without a format
specification is tried on every file that was not parsed by a parser with a
matching signature.

`ParseFileObject` must raise `WrongParser` if the file is not supported by the
parser. Once the parser has determined the file is supported, issues with the
file can be reported with `parser_mediator.ProduceWarning()`.

### The data format definition

The parser uses a [dtFabric](https://github.com/libyal/dtfabric) definition
of the data format, which is stored next to the parser and is loaded by
`dtfabric_helper.DtFabricHelper` from the `_DEFINITION_FILE` class constant.

```
plaso/parsers/safari_cookies.yaml
```

~~~~yaml
name: binarycookies_file_header
type: structure
attributes:
  byte_order: big-endian
members:
- name: signature
  type: stream
  element_data_type: byte
  number_of_elements: 4
  value: "cook"
- name: number_of_pages
  data_type: uint32
~~~~

The parser maps a data type definition with `self._GetDataTypeMap()` and
reads the corresponding data with `self._ReadStructureFromFileObject()` or
`self._ReadStructureFromByteStream()`.

### Registering a parser

To ensure the parser is registered automatically add an import to:

```
plaso/parsers/__init__.py
```

~~~~python
from plaso.parsers import safari_cookies
~~~~

When plaso.parsers is imported this will load the safari_cookies submodule
`safari_cookies.py`.

To enable the parser by default for a specific operating system, add it to
the corresponding [parser preset](../user/Using-log2timeline.html#parsers-and-presets)
in `plaso/data/presets.yaml`, for example `binary_cookies` is part of the
`webhist` preset.

### The event data

~~~~python
from plaso.containers import events


class SafariBinaryCookieEventData(events.EventData):
    """Safari binary cookie event data.

    Attributes:
      cookie_name (str): cookie name.
      creation_time (dfdatetime.DateTimeValues): date and time the cookie was created.
      ...
    """

    DATA_TYPE = "safari:cookie:entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.cookie_name = None
        self.creation_time = None
        ...
~~~~

Date and time values are stored as [dfDateTime](https://github.com/log2timeline/dfdatetime)
objects, for example `dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)`.
For the naming conventions of the data type and the supported value types see
the [style guide](Style-guide.html#event-data-attribute-containers).

The parser passes the event data to `parser_mediator.ProduceEventData()`.

~~~~python
        event_data = SafariBinaryCookieEventData()
        event_data.cookie_name = self._ParseCString(page_data, data_offset)
        ...
        parser_mediator.ProduceEventData(event_data)
~~~~

### The unit test

To ensure the parser is and remains working it is necessary to write a unit
test. Next create the parser unit test and add it to the `tests/parsers/`
directory.

```
tests/parsers/safari_cookies.py
```

~~~~python
#!/usr/bin/env python3
"""Tests for the Safari cookie parser."""

import unittest

from plaso.parsers import safari_cookies

from tests.parsers import test_lib


class SafariCookieParserTest(test_lib.ParserTestCase):
    """Tests for the Safari cookie parser."""

    def testParseFile(self):
        """Tests the Parse function on a Safari binary cookies file."""
        parser = safari_cookies.BinaryCookieParser()
        storage_writer = self._ParseFile(["Cookies.binarycookies"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 106)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "cookie_name": "fpc",
            "creation_time": "2013-07-08T17:24:30.000000+00:00",
            "data_type": "safari:cookie:entry",
            ...
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 26)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
~~~~

The unit test can be run with:

```
PYTHONPATH=. python ./tests/parsers/safari_cookies.py
```

### The timeliner configuration

To have Plaso generate events from the extracted event data the timeliner
configuration `plaso/data/timeliner.yaml` needs to be extended with a
definition for the `safari:cookie:entry` data type.

~~~~yaml
data_type: 'safari:cookie:entry'
attribute_mappings:
- name: 'creation_time'
  description: 'Creation Time'
- name: 'expiration_time'
  description: 'Expiration Time'
place_holder_event: true
~~~~

### The message formatter configuration

To have Plaso generate human readable message of the event data the formatter
configuration `plaso/data/formatters/` needs to be extended with a definition
for the `safari:cookie:entry` data type.

The event message format is defined in `plaso/data/formatters/*.yaml`.

~~~~yaml
type: 'conditional'
data_type: 'safari:cookie:entry'
message:
- '{url}'
...
short_message:
- '{url}'
...
short_source: 'WEBHIST'
source: 'Safari Cookies'
~~~~

For more information about the configuration file format see:
[message formatting](../user/Output-and-formatting.html#message-formatting)

## Troubleshooting

* If the parser is not listed by `log2timeline.py --parsers list`, check that it is imported in `plaso/parsers/__init__.py` and registered with `manager.ParsersManager.RegisterParser()`.
* If the parser is not applied to a file, check its format specification, or test it on the file with only the parser enabled, for example: `log2timeline.py --parsers binary_cookies --storage-file test.plaso test_data/Cookies.binarycookies`.
* Use `pinfo.py --sections events,warnings test.plaso` to see the number of events generated per parser and the warnings the parser produced.
* If events are missing in the output, check that the data type is defined in `plaso/data/timeliner.yaml`. To check the attributes of the event data definitions run `PYTHONPATH=. ./utils/export_event_data.py --strict`.
