# -*- coding: utf-8 -*-
"""The default plugin for parsing OLE Compound Files (OLECF)."""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OLECFItemEventData(events.EventData):
  """OLECF item event data.

  Attributes:
    name (str): name of the OLE Compound File item.
    size (int): data size of the OLE Compound File item.
  """

  DATA_TYPE = 'olecf:item'

  def __init__(self):
    """Initializes event data."""
    super(OLECFItemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.name = None
    self.size = None


class DefaultOLECFPlugin(interface.OLECFPlugin):
  """Class to define the default OLECF file plugin."""

  NAME = 'olecf_default'
  DATA_FORMAT = 'Generic OLE compound item'

  def _ParseItem(self, parser_mediator, olecf_item):
    """Parses an OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      bool: True if an event was produced.
    """
    result = False

    event_data = OLECFItemEventData()
    event_data.name = olecf_item.name
    event_data.size = olecf_item.size

    creation_time, modification_time = self._GetTimestamps(olecf_item)
    if creation_time:
      date_time = dfdatetime_filetime.Filetime(timestamp=creation_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)
      result = True

    if modification_time:
      date_time = dfdatetime_filetime.Filetime(timestamp=modification_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)
      result = True

    for sub_item in olecf_item.sub_items:
      if self._ParseItem(parser_mediator, sub_item):
        result = True

    return result

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from an OLECF file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(DefaultOLECFPlugin, self).Process(parser_mediator, **kwargs)

    if not root_item:
      raise ValueError('Root item not set.')

    if not self._ParseItem(parser_mediator, root_item):
      event_data = OLECFItemEventData()
      event_data.name = root_item.name
      event_data.size = root_item.size

      # If no event was produced, produce at least one for the root item.
      date_time = dfdatetime_semantic_time.NotSet()
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)


olecf.OLECFParser.RegisterPlugin(DefaultOLECFPlugin)
