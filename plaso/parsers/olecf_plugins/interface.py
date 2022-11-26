# -*- coding: utf-8 -*-
"""This file contains the necessary interface for OLECF plugins."""

import abc

from dfdatetime import filetime as dfdatetime_filetime

from plaso.parsers import logger
from plaso.parsers import plugins


class OLECFPlugin(plugins.BasePlugin):
  """The OLECF parser plugin interface."""

  NAME = 'olecf_plugin'
  DATA_FORMAT = 'OLE compound file'

  # List of tables that should be present in the database, for verification.
  REQUIRED_ITEMS = frozenset([])

  def _GetCreationTime(self, olecf_item):
    """Retrieves the creation date and time from an OLECF item.

    Args:
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      dfdatetime.Filetime: creation date and time or None if not available.
    """
    if not olecf_item:
      return None

    try:
      filetime = olecf_item.get_creation_time_as_integer()
    except OverflowError as exception:
      logger.warning(
          'Unable to read the creation time with error: {0!s}'.format(
              exception))
      return None

    # Office template documents sometimes contain a creation time
    # of -1 (0xffffffffffffffff).
    if filetime in (0, 0xffffffffffffffff):
      return None

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  def _GetModificationTime(self, olecf_item):
    """Retrieves the modification date and time from an OLECF item.

    Args:
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      dfdatetime.Filetime: creation date and time or None if not available.
    """
    if not olecf_item:
      return None

    try:
      filetime = olecf_item.get_modification_time_as_integer()
    except OverflowError as exception:
      logger.warning(
          'Unable to read the modification time with error: {0!s}'.format(
              exception))
      return None

    if filetime == 0:
      return None

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from an OLECF file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.
    """
