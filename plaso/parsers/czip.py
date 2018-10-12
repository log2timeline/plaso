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
  """Handles compound ZIP files and provides a slim interface to list and read
  files from it, acting as a proxy.

  The Plaso engine calls parsers by their Parse() method. The Parse() function
  checks if the ZIP is valid and calls plugins (CompoundZIPPlugin) registered
  through the interface by their Process() to produce event objects.

  Plugins are how this parser understands the content inside a compound ZIP
  file, each plugin holds logic specific to a particular archive file. See the
  czip_plugins / directory for examples of how czip plugins are implemented.
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

    # Some non-ZIP files pass the first test but will fail with a negative
    # seek (IOError) or another error.
    try:
      zip_file = zipfile.ZipFile(file_object, 'r', allowZip64=True)
      zip_file.close()
    except (zipfile.BadZipfile, struct.error, zipfile.LargeZipFile):
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, 'Bad Zip file.'))

    with zipfile.ZipFile(file_object, 'r', allowZip64=True) as zip_file:
      name_list = zip_file.namelist()
      for plugin in self._plugins:
        try:
          plugin.UpdateChainAndProcess(
              parser_mediator, zip_file=zip_file, name_list=name_list)
        except errors.WrongCompoundZIPPlugin as exception:
          logger.debug('[{0:s}] wrong plugin: {1!s}'.format(
              self.NAME, exception))


manager.ParsersManager.RegisterParser(CompoundZIPParser)
