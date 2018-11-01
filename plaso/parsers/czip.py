# -*- coding: utf-8 -*-
"""This file contains a parser for compound ZIP files."""

from __future__ import unicode_literals

import struct
import zipfile

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class CompoundZIPParser(interface.FileObjectParser):
  """Shared functionality for parsing compound zip files.

  Compound zip files are zip files used as containers to create another file
  format, as opposed to archives of unrelated files.
  """

  NAME = 'czip'
  DESCRIPTION = 'Parser for compound ZIP files.'

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a compound ZIP file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    display_name = parser_mediator.GetDisplayName()

    if not zipfile.is_zipfile(file_object):
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, 'Not a Zip file.'))

    try:
      zip_file = zipfile.ZipFile(file_object, 'r', allowZip64=True)
      self._ProcessZipFileWithPlugins(parser_mediator, zip_file)
      zip_file.close()

    # Some non-ZIP files return true for is_zipfile but will fail with a
    # negative seek (IOError) or another error.
    except (zipfile.BadZipfile, struct.error) as exception:
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file: {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))

  def _ProcessZipFileWithPlugins(self, parser_mediator, zip_file):
    """Processes a zip file using all compound zip files.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed in ParseFileObject().
    """
    archive_members = zip_file.namelist()
    for plugin in self._plugins:
      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, zip_file=zip_file, archive_members=archive_members)
      except errors.WrongCompoundZIPPlugin as exception:
        logger.debug('[{0:s}] wrong plugin: {1!s}'.format(
            self.NAME, exception))


manager.ParsersManager.RegisterParser(CompoundZIPParser)
