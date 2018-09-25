# How to write a parser

## Introduction
This page is intended to give you an introduction into developing a parser for plaso.

* First a step-by-step example is provided to create a simple binary parser for the Safari Cookies.binarycookies file.
* At bottom are some common troubleshooting tips that others have run into before you.

This page assumes you have at least a basic understanding of programming in Python and use of git.

## Format

Before you can write a binary file parser you will need to have a good understanding of the file format. A description of the Safari Cookies.binarycookies format can be found [here](https://github.com/libyal/assorted/blob/master/documentation/Safari%20Cookies.asciidoc).

## Parsers vs. Plugins
Before starting work on a parser, check if Plaso already has a parser that handles the underlying format of the file you're parsing. Plaso currently supports plugins for the following file formats:
* Bencode
* Web Browser Cookies
* ESEDB
* OLECF
* Plist
* SQLite
* [Syslog](How-to-write-a-Syslog-plugin.md)
* Windows Registry

If the artifact you're trying to parse is in one of these formats, you need to write a plugin of the appropriate type, rather than a parser.

For our example, however, the Safari Cookies.binarycookies file is in its own binary format, so a separate parser is appropriate.

## Test data

First we make a representative test file and add it to the test_data/ directory, in our example:
```
test_data/Cookies.binarycookies
```

**Make sure that the test file does not contain sensitive or copyrighted material.**

## Parsers, formatters, events and event data

* parser; subclass of plaso.parsers.interface.FileObjectParser, that extracts events from the content of a file.
* formatter (or event formatter); subclass of plaso.formatters.interface.EventFormatter, that generates a human readable description of the event data. 
* event; subclass of plaso.containers.events.EventObject, that represents [an event](Scribbles-about-events.md#what-is-an-event)
* event data; subclass of plaso.containers.events.EventData, that represents data related to the event.

### Writing the parser

#### Registering the parser

Add an import for the parser to:
```
plaso/parsers/__init__.py
```

```
from plaso.parsers import safari_cookies
```

When plaso.parsers is imported this will load the safari_cookies module (safari_cookies.py).

The parser class `BinaryCookieParser` is registered using `manager.ParsersManager.RegisterParser(BinaryCookieParser)`.

```
plaso/parsers/safari_cookies.py
```

~~~~
# -*- coding: utf-8 -*-
"""Parser for Safari Binary Cookie files."""

from plaso.parsers import interface
from plaso.parsers import manager


class BinaryCookieParser(interface.FileObjectParser):
  """Parser for Safari Binary Cookie files."""

  NAME = u'binary_cookies'
  DESCRIPTION = u'Parser for Safari Binary Cookie files.'

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

* `NAME`
* `DESCRIPTION`




### Writing the event formatter

```
plaso/formatters/safari_cookies.py
```