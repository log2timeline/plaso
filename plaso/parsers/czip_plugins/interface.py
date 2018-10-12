# -*- coding: utf-8 -*-
"""czip_interface contains basic interface for compound ZIP plugins within
Plaso.

CompoundZIPPlugin defines the attributes necessary for registration, discovery
and operation of plugins for czip files which will be used by CompoundZIPParser.
"""

from __future__ import unicode_literals

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins

class CompoundZIPPlugin(plugins.BasePlugin):
  """This is an "abstract" class from which plugins should be based."""

  # REQUIRED_PATHS is a list of items required by a plugin.
  # This is used to understand whether a plugin is suited for a given compound
  # ZIP archive.
  # This is expected to be overridden by actual plugins.
  # Ex. frozenset(['[Content_Types].xml', '_rels/.rels', 'docProps/core.xml'])
  REQUIRED_PATHS = frozenset(['any'])

  NAME = 'czip'

  def __init__(self):
    super(CompoundZIPPlugin, self).__init__()
    self._zip_file = None

  def InspectArchive(self, parser_mediator):
    """Inspects a compound ZIP archive looking for data.

    This is the main method that a compound ZIP plugin needs to implement.

    Upon successful file check (always if you get down to this point) you will
    find a file-like object corresponding to your archive in self._zip_file.
    Feel free to implement the logic you prefer.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, zip_file, name_list):
    """Determine if this is the correct plugin; if so proceed with processing.

    Process() checks if the current czip file being processed is a match for
    a plugin by comparing REQUIRED_PATHS: if they match processing continues;
    else raise WrongCompoundZIPPlugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the archive file, already opened and
          auto-closed.
      name_list (list[str]): a convenience argument so we don't call
          zip_file.namelist() once per plugin.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    if not set(name_list).issuperset(self.REQUIRED_PATHS):
      raise errors.WrongCompoundZIPPlugin(self.NAME)

    # This will raise if unhandled keyword arguments are passed.
    super(CompoundZIPPlugin, self).Process(parser_mediator)

    logger.debug('Compound ZIP Plugin used: {0:s}'.format(self.NAME))

    self._zip_file = zip_file
    self.InspectArchive(parser_mediator)
