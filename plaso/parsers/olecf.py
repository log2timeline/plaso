# -*- coding: utf-8 -*-
"""Parser for OLE Compound Files (OLECF)."""

import logging

import pyolecf

from plaso import dependencies
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


dependencies.CheckModuleVersion(u'pyolecf')


class OLECFParser(interface.FileObjectParser):
  """Parses OLE Compound Files (OLECF)."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'olecf'
  DESCRIPTION = u'Parser for OLE Compound Files (OLECF).'

  _plugin_classes = {}

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

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an OLE Compound File (OLECF) file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.
    """
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(parser_mediator.codepage)

    try:
      olecf_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionError(
          u'unable to open file with error: {0:s}'.format(exception))
      return

    root_item = olecf_file.root_item
    if not root_item:
      return

    # Get a list of all items in the root item from the OLECF file.
    item_names = [item.name for item in root_item.sub_items]

    # Compare the list of available plugin objects.
    # We will try to use every plugin against the file (except
    # the default plugin) and run it. Only if none of the plugins
    # works will we use the default plugin.

    # TODO: add a parser filter.
    for plugin_object in self._plugin_objects:
      try:
        plugin_object.UpdateChainAndProcess(
            parser_mediator, root_item=root_item, item_names=item_names)
      except errors.WrongPlugin:
        logging.debug(
            u'[{0:s}] plugin: {1:s} cannot parse the OLECF file: {2:s}'.format(
                self.NAME, plugin_object.NAME,
                parser_mediator.GetDisplayName()))

    if self._default_plugin:
      self._default_plugin.UpdateChainAndProcess(
          parser_mediator, root_item=root_item, item_names=item_names)

    olecf_file.close()


manager.ParsersManager.RegisterParser(OLECFParser)
