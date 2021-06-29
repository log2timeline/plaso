# -*- coding: utf-8 -*-
"""This file contains the necessary interface for OLECF plugins."""

import abc

from plaso.parsers import logger
from plaso.parsers import plugins


class OLECFPlugin(plugins.BasePlugin):
  """The OLECF parser plugin interface."""

  NAME = 'olecf_plugin'
  DATA_FORMAT = 'OLE compound file'

  # List of tables that should be present in the database, for verification.
  REQUIRED_ITEMS = frozenset([])

  def _GetTimestamps(self, olecf_item):
    """Retrieves the timestamps from an OLECF item.

    Args:
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      tuple[int, int]: creation and modification FILETIME timestamp.
    """
    if not olecf_item:
      return None, None

    try:
      creation_time = olecf_item.get_creation_time_as_integer()
    except OverflowError as exception:
      logger.warning(
          'Unable to read the creation time with error: {0!s}'.format(
              exception))
      creation_time = 0

    try:
      modification_time = olecf_item.get_modification_time_as_integer()
    except OverflowError as exception:
      logger.warning(
          'Unable to read the modification time with error: {0!s}'.format(
              exception))
      modification_time = 0

    # If no useful events, return early.
    if not creation_time and not modification_time:
      return None, None

    # Office template documents sometimes contain a creation time
    # of -1 (0xffffffffffffffff).
    if creation_time == 0xffffffffffffffff:
      creation_time = 0

    return creation_time, modification_time

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from an OLECF file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.
    """
