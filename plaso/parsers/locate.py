# -*- coding: utf-8 -*-
"""Parser for locate/updatedb database files."""

from plaso.parsers import interface
from plaso.parsers import manager


class LocateDatabaseParser(interface.FileObjectParser):
    """Parser for locate/updatedb database files"""

    NAME = 'locate_database'
    DATA_FORMAT = 'Locate Database file'

    def ParseFileObject(self, parser_mediator, file_object, **kwargs):
        """Parses a locate/updatedb database file-like object.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          file_object (dfvfs.FileIO): file-like object to be parsed.

        Raises:
          UnableToParseFile: when the file cannot be parsed, this will signal
              the event extractor to apply other parsers.
        """
        pass


manager.ParsersManager.RegisterParser(LocateDatabaseParser)
