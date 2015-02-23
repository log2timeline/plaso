# -*- coding: utf-8 -*-
"""Parser for Extensible Storage Engine (ESE) database files (EDB)."""

import logging

import pyesedb

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


if pyesedb.get_version() < '20140301':
  raise ImportWarning(u'EseDbParser requires at least pyesedb 20140301.')


class EseDbCache(plugins.BasePluginCache):
  """A cache storing query results for ESEDB plugins."""

  def StoreDictInCache(self, attribute_name, dict_object):
    """Store a dict object in cache.

    Args:
      attribute_name: The name of the attribute.
      dict_object: A dict object.
    """
    setattr(self, attribute_name, dict_object)


class EseDbParser(interface.BasePluginsParser):
  """Parses Extensible Storage Engine (ESE) database files (EDB)."""

  NAME = u'esedb'
  DESCRIPTION = u'Parser for Extensible Storage Engine (ESE) database files.'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(EseDbParser, self).__init__()
    self._plugins = EseDbParser.GetPluginObjects()

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\xef\xcd\xab\x89', offset=4)
    return format_specification

  def Parse(self, parser_mediator, **kwargs):
    """Parses an ESE database file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object = parser_mediator.GetFileObject()
    try:
      self.ParseFileObject(parser_mediator, file_object)
    finally:
      file_object.close()

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an ESE database file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    esedb_file = pyesedb.file()

    try:
      esedb_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    # Compare the list of available plugins.
    cache = EseDbCache()
    for plugin_object in self._plugins:
      try:
        plugin_object.UpdateChainAndProcess(
           parser_mediator, database=esedb_file, cache=cache)
      except errors.WrongPlugin:
        logging.debug((
            u'[{0:s}] plugin: {1:s} cannot parse the ESE database: '
            u'{2:s}').format(
                self.NAME, plugin_object.NAME,
                parser_mediator.GetDisplayName()))

    # TODO: explicitly clean up cache.

    esedb_file.close()


manager.ParsersManager.RegisterParser(EseDbParser)
