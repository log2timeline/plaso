# -*- coding: utf-8 -*-
"""The default plugin for parsing OLE Compound Files (OLECF)."""

from plaso.containers import events
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OLECFItemEventData(events.EventData):
  """OLECF item event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the item.
    modification_time (dfdatetime.DateTimeValues): modification date and time
        of the item.
    name (str): name of the OLE Compound File item.
    size (int): data size of the OLE Compound File item.
  """

  DATA_TYPE = 'olecf:item'

  def __init__(self):
    """Initializes event data."""
    super(OLECFItemEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.modification_time = None
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
          and other components, such as storage and dfVFS.
      olecf_item (pyolecf.item): OLECF item.

    Returns:
      bool: True if an event was produced.
    """
    event_data = OLECFItemEventData()
    event_data.creation_time = self._GetCreationTime(olecf_item)
    event_data.modification_time = self._GetModificationTime(olecf_item)
    event_data.name = olecf_item.name
    event_data.size = olecf_item.size

    parser_mediator.ProduceEventData(event_data)

    for sub_item in olecf_item.sub_items:
      self._ParseItem(parser_mediator, sub_item)

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from an OLECF file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(DefaultOLECFPlugin, self).Process(parser_mediator, **kwargs)

    if not root_item:
      raise ValueError('Root item not set.')

    self._ParseItem(parser_mediator, root_item)


olecf.OLECFParser.RegisterPlugin(DefaultOLECFPlugin)
