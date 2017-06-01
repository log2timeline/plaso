# -*- coding: utf-8 -*-
"""The default plugin for parsing OLE Compound Files (OLECF)."""

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OLECFItemEvent(time_events.DateTimeValuesEvent):
  """Convenience class for an OLECF item event."""

  DATA_TYPE = u'olecf:item'

  def __init__(self, date_time, date_time_description, olecf_item):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
      olecf_item (pyolecf.item): OLECF item.
    """
    super(OLECFItemEvent, self).__init__(date_time, date_time_description)
    self.name = olecf_item.name

    # TODO: need a better way to express the original location of the
    # original data.
    self.offset = 0

    # TODO: have pyolecf return the item type here.
    # self.type = olecf_item.type
    self.size = olecf_item.size


class DefaultOLECFPlugin(interface.OLECFPlugin):
  """Class to define the default OLECF file plugin."""

  NAME = u'olecf_default'
  DESCRIPTION = u'Parser for a generic OLECF item.'

  def _ParseItem(self, parser_mediator, olecf_item):
    """Parses an OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      bool: True if an event was produced.
    """
    event = None
    result = False

    creation_time, modification_time = self._GetTimestamps(olecf_item)

    if creation_time:
      date_time = dfdatetime_filetime.Filetime(timestamp=creation_time)
      event = OLECFItemEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION, olecf_item)
      parser_mediator.ProduceEvent(event)

    if modification_time:
      date_time = dfdatetime_filetime.Filetime(timestamp=modification_time)
      event = OLECFItemEvent(
          date_time, definitions.TIME_DESCRIPTION_MODIFICATION, olecf_item)
      parser_mediator.ProduceEvent(event)

    if event:
      result = True

    for sub_item in olecf_item.sub_items:
      if self._ParseItem(parser_mediator, sub_item):
        result = True

    return result

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Parses an OLECF file.

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
      raise ValueError(u'Root item not set.')

    if not self._ParseItem(parser_mediator, root_item):
      # If no event was produced, produce at least one for the root item.
      date_time = dfdatetime_semantic_time.SemanticTime(u'Not set')
      event = OLECFItemEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION, root_item)
      parser_mediator.ProduceEvent(event)


olecf.OLECFParser.RegisterPlugin(DefaultOLECFPlugin)
