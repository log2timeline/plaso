# -*- coding: utf-8 -*-
"""Interface for compound zip file plugins.
"""

from __future__ import unicode_literals

import abc

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins

class CompoundZIPPlugin(plugins.BasePlugin):
  """Compound zip parser plugin."""

  # REQUIRED_PATHS is a list of paths required by a plugin.
  # This is used to understand whether a plugin is suited for a given compound
  # ZIP file.
  # This must be overridden by actual plugins.
  REQUIRED_PATHS = frozenset()

  NAME = 'czip'

  @abc.abstractmethod
  def InspectZipFile(self, parser_mediator, zip_file):
    """Inspects a compound ZIP file and produces events.

    This is the main method that a compound ZIP plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed by the parser logic in czip.py.
    """

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, zip_file, archive_members):
    """Determines if this is the correct plugin; if so proceed with processing.

    This method checks if the zip file being contains the paths specified in
    REQUIRED_PATHS. If all paths are present, the plugin logic processing
    continues in InspectZipFile.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed by the parser logic in czip.py.
      archive_members (list[str]): file paths in the archive.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
      ValueError: if a subclass has not specified REQUIRED_PATHS.
    """
    if not self.REQUIRED_PATHS:
      raise ValueError('REQUIRED_PATHS not specified')

    if not set(archive_members).issuperset(self.REQUIRED_PATHS):
      raise errors.WrongCompoundZIPPlugin(self.NAME)

    logger.debug('Compound ZIP Plugin used: {0:s}'.format(self.NAME))

    self.InspectZipFile(parser_mediator, zip_file)
