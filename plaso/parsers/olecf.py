# -*- coding: utf-8 -*-
"""Parser for OLE Compound Files (OLECF)."""

import logging

import pyolecf

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


if pyolecf.get_version() < '20131012':
  raise ImportWarning(u'OleCfParser requires at least pyolecf 20131012.')


class OleCfParser(interface.BasePluginsParser):
  """Parses OLE Compound Files (OLECF)."""

  NAME = u'olecf'
  DESCRIPTION = u'Parser for OLE Compound Files (OLECF).'

  _plugin_classes = {}

  def __init__(self):
    """Initializes a parser object."""
    super(OleCfParser, self).__init__()
    self._plugins = OleCfParser.GetPluginObjects()

    for list_index, plugin_object in enumerate(self._plugins):
      if plugin_object.NAME == u'olecf_default':
        self._default_plugin = self._plugins.pop(list_index)
        break

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification."""
    format_specification = specification.FormatSpecification(cls.NAME)

    # OLECF
    format_specification.AddNewSignature(
        b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', offset=0)

    # OLECF beta
    format_specification.AddNewSignature(
        b'\x0e\x11\xfc\x0d\xd0\xcf\x11\x0e', offset=0)

    return format_specification

  def Parse(self, parser_mediator, **kwargs):
    """Parses an OLE Compound File (OLECF).

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
    """Parses an OLE Compound File (OLECF) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      olecf_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    # Get a list of all root items from the OLE CF file.
    root_item = olecf_file.root_item
    item_names = [item.name for item in root_item.sub_items]

    # Compare the list of available plugins.
    # We will try to use every plugin against the file (except
    # the default plugin) and run it. Only if none of the plugins
    # works will we use the default plugin.
    parsed = False
    for plugin_object in self._plugins:
      try:
        plugin_object.UpdateChainAndProcess(
            parser_mediator, root_item=root_item, item_names=item_names)
      except errors.WrongPlugin:
        logging.debug(
            u'[{0:s}] plugin: {1:s} cannot parse the OLECF file: {2:s}'.format(
                self.NAME, plugin_object.NAME,
                parser_mediator.GetDisplayName()))

    # Check if we still haven't parsed the file, and if so we will use
    # the default OLECF plugin.
    if not parsed and self._default_plugin:
      self._default_plugin.UpdateChainAndProcess(
          parser_mediator, root_item=root_item, item_names=item_names)

    olecf_file.close()


manager.ParsersManager.RegisterParser(OleCfParser)
