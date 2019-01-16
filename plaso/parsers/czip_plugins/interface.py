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

  def CheckZipFile(self, zip_file, archive_members):
    """Checks if the zip file being contains the paths specified in
       REQUIRED_PATHS. If all paths are present, the plugin logic processing
       continues in InspectZipFile.
       If a czip's plugin overrides this method, another logic will be applied.

       Args:
         zip_file (zipfile.ZipFile): the zip file. It should not be closed in
             this method, but will be closed by the parser logic in czip.py.
         archive_members (list[str]): file paths in the archive.

       Returns:
         true if the required paths are set and the archive members' set is a super set of the
         required paths' set
    """
    return self.REQUIRED_PATHS and set(archive_members).issuperset(self.REQUIRED_PATHS)

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, zip_file, archive_members):
    """Determines if this is the correct plugin; if so proceed with processing.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed by the parser logic in czip.py.
      archive_members (list[str]): file paths in the archive.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
      ValueError: if a subclass has not specified REQUIRED_PATHS or the regex didn't validate the
        specific file.
    """

    if not self.CheckZipFile(zip_file, archive_members):
      raise errors.WrongCompoundZIPPlugin(self.NAME)

    logger.debug('Compound ZIP Plugin used: {0:s}'.format(self.NAME))

    self.InspectZipFile(parser_mediator, zip_file)
