# How to write a parser or (parser) plugin

## Introduction

This page is intended to give you an introduction into developing a parser for
Plaso.

* A step-by-step example is provided to create a simple binary parser for the Safari Cookies.binarycookies file.
* At bottom are some common troubleshooting tips that others have run into before you.

This page assumes you have at least a basic understanding of programming in
Python and use of git.

### Terminology

* event; a subclass of [EventObject](../api/plaso.containers.html#plaso.containers.events.EventObject) which represents [an event](Scribbles-about-events.md#what-is-an-event)
* event data; a subclass of [EventData](../api/plaso.containers.html#plaso.containers.events.EventData) which represents data related to the event.
* event data stream; a subclass of [EventDataStream](../api/plaso.containers.html#plaso.containers.events.EventDataStream) which represents the data stream which the event data originated from.
* message formatter; a configuration driven subsystem of Plaso that generates a human readable message of the event data.
* timeliner; a configuration driven subsystem of Plaso that generates events from event data.
* parser; a subclass of [FileObjectParser](../api/plaso.parsers.html#plaso.parsers.interface.FileObjectParser) that extracts event data from a file.
* parser plugin; an extension of existing parser, such as the SQLite parser, that that extracts event data from a file.

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
* SQLite databases
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
# -*- coding: utf-8 -*-
"""Parser for Safari Binary Cookie files."""

from plaso.parsers import interface
from plaso.parsers import manager


class BinaryCookieParser(interface.FileObjectParser):
  """Parser for Safari Binary Cookie files."""

  NAME = 'binary_cookies'
  DATA_FORMAT = 'Safari Binary Cookie file'

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Safari binary cookie file-like object.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_object (dfvfs.FileIO): file-like object to be parsed.

    Raises:
      WrongParser: when the format is not supported by the parser, this will
          signal the event extractor to apply other parsers.
    """
    ...


manager.ParsersManager.RegisterParser(BinaryCookieParser)
~~~~

`manager.ParsersManager.RegisterParser(BinaryCookieParser)` is used to
register the parser with the unique name `binary_cookies`.

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

### The event data

~~~~python
from plaso.containers import events


class SafariBinaryCookieEventData(events.EventData):
  """Safari binary cookie event data.

  Attributes:
    cookie_name (str): cookie name.
    ...
  """

  DATA_TYPE = 'safari:cookie:entry'

  def __init__(self):
    """Initializes event data."""
    super(SafariBinaryCookieEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    ...
~~~~

### The unit test

To ensure the parser is and remains working it is necessary to write a unit
test. Next create the parser unit test and add it to the `tests/parsers/`
directory.

```
test/parsers/safari_cookies.py
```

~~~~python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Safari cookie parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import safari_cookies

from tests.parsers import test_lib


class SafariCookieParserTest(test_lib.ParserTestCase):
  """Tests for the Safari cookie parser."""

  def testParseFile(self):
    """Tests the Parse function on a Safari binary cookies file."""
    ...


if __name__ == '__main__':
  unittest.main()
~~~~

### The timeliner configuration

To have Plaso generate events from the extracted event data the timeliner
configuration `data/timeliner.yaml` needs to be extended with a definition
for the `safari:cookie:entry` data type.

~~~~yaml
data_type: 'safari:cookie:entry'
attribute_mappings:
- name: 'creation_time'
  description: 'Creation Time'
place_holder_event: true
~~~~

### The message formatter configuration

To have Plaso generate human readable message of the event data the formatter
configuration `data/formatters/` needs to be extended with a definition for
the `safari:cookie:entry` data type.

The event message format is defined in `data/formatters/*.yaml`.

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
