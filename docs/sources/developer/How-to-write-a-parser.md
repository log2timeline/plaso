# How to write a parser

## Introduction

This page is intended to give you an introduction into developing a parser for
Plaso.

* First a step-by-step example is provided to create a simple binary parser
for the Safari Cookies.binarycookies file.
* At bottom are some common troubleshooting tips that others have run into
before you.

This page assumes you have at least a basic understanding of programming in
Python and use of git.

## Format

Before you can write a binary file parser you will need to have a good
understanding of the file format. Several things can help here:

* having a diverse set of test data, preferable test data that is reproducible. Examples of how to create reprocible test data can be found [here](https://github.com/dfirlabs)
* having format specifications

## Parsers vs. Plugins

Before starting work on a parser, check if Plaso already has a parser that
handles the underlying format of the file you're parsing. Plaso currently
supports plugins for the following file formats:
* Bencode
* Compound zip files
* Web Browser Cookies
* ESEDB
* OLECF
* Plist
* SQLite
* [Syslog](How-to-write-a-Syslog-plugin.md)
* Windows Registry

If the artifact you're trying to parse is in one of these formats, you need to
write a plugin of the appropriate type, rather than a parser.

For our example, however, the Safari Cookies.binarycookies file is in its own
binary format, so a separate parser is appropriate.

A description of the Safari Cookies.binarycookies format can be found
[here](https://github.com/libyal/dtformats/blob/main/documentation/Safari%20Cookies.asciidoc).

## Test data

First we make a representative test file and add it to the `test_data/`
directory, in our example:

```
test_data/Cookies.binarycookies
```

**Make sure that the test file does not contain sensitive or copyrighted
material.**

## Parsers, formatters, events and event data

* parser; a subclass of [FileObjectParser](../api/plaso.parsers.html#plaso.parsers.interface.FileObjectParser)
 that extracts events from the content of a file.
* formatter (or event formatter); a subclass of
[EventFormatter](../api/plaso.formatters.html#plaso.formatters.interface.EventFormatter) which generates a human readable
description of the event data.
* event; a subclass of [EventObject](../api/plaso.containers.html#plaso.containers.events.EventObject) which represents
[an event](Scribbles-about-events.md#what-is-an-event)
* event data; a subclass of [EventData](../api/plaso.containers.html#plaso.containers.events.EventData) which represents
data related to the event.

### Writing the parser

#### Registering the parser

Add an import for the parser to:

```
plaso/parsers/__init__.py
```

It should look like this:

~~~~python
from plaso.parsers import safari_cookies
~~~~

When plaso.parsers is imported this will load the safari_cookies module
`safari_cookies.py`.

The parser class `BinaryCookieParser` is registered using
`manager.ParsersManager.RegisterParser(BinaryCookieParser)`.

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
      UnableToParseFile: when the file cannot be parsed, this will signal
          the event extractor to apply other parsers.
    """
    ...


manager.ParsersManager.RegisterParser(BinaryCookieParser)
~~~~

### Writing the message formatter

The event message format is defined in `data/formatters/*.yaml`.

For more information about the configuration file format see:
[message formatting](../user/Output-and-formatting.html#message-formatting)

