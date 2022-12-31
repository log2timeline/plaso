# -*- coding: utf-8 -*-
"""Null device output module."""

from plaso.output import interface
from plaso.output import manager


class NullOutputModule(interface.OutputModule):
  """Null device output module."""

  NAME = 'null'
  DESCRIPTION = 'Output module that does not output anything.'

  # pylint: disable=unused-argument

  def _GetFieldValues(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Retrieves the output field values.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, str]: output field values per name.
    """
    return {}

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    return


manager.OutputManager.RegisterOutput(NullOutputModule)
