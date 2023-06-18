# -*- coding: utf-8 -*-
"""This file contains the output module interface class."""

import abc

from plaso.output import logger


class OutputModule(object):
  """Output module interface."""

  NAME = ''
  DESCRIPTION = ''

  # Value to indicate the output module supports outputting additional fields.
  SUPPORTS_ADDITIONAL_FIELDS = False

  # Value to indicate the output module supports outputting custom fields.
  SUPPORTS_CUSTOM_FIELDS = False

  # Value to indicate the output module writes to an output file.
  WRITES_OUTPUT_FILE = False

  @abc.abstractmethod
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

  @abc.abstractmethod
  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """

  def _ReportEventError(self, event, event_data, error_message):
    """Reports an event related error.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      error_message (str): error message.
    """
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()
    display_name = getattr(event_data, 'display_name', None) or 'N/A'

    parser_chain = getattr(event_data, '_parser_chain', None)
    if not parser_chain:
      # Note that parser is kept for backwards compatibility.
      parser_chain = getattr(event_data, 'parser', None) or 'N/A'

    error_message = (
        'Event: {0!s} data type: {1:s} display name: {2:s} '
        'parser chain: {3:s} with error: {4:s}').format(
            event_identifier_string, event_data.data_type, display_name,
            parser_chain, error_message)
    logger.error(error_message)

  def Close(self):
    """Closes the output."""
    return

  def GetMissingArguments(self):
    """Retrieves arguments required by the module that have not been specified.

    Returns:
      list[str]: names of argument that are required by the module and have
          not been specified.
    """
    return []

  def Open(self, **kwargs):  # pylint: disable=unused-argument
    """Opens the output."""
    return

  def WriteFieldValues(
      self, output_mediator, event, event_data, event_data_stream, event_tag):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    field_values = self._GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

    self._WriteFieldValues(output_mediator, field_values)

  def WriteFieldValuesOfMACBGroup(self, output_mediator, macb_group):
    """Writes field values of a MACB group to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      macb_group (list[tuple[event, event_data, event_data_stream, event_tag]]):
          group of event, event_data, event_data_stream and event_tag objects
          with identical timestamps, attributes and values.
    """
    for event, event_data, event_data_stream, event_tag in macb_group:
      self.WriteFieldValues(
          output_mediator, event, event_data, event_data_stream, event_tag)

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event
    is written, such as writing a file footer.
    """
    return

  def WriteHeader(self, output_mediator):  # pylint: disable=unused-argument
    """Writes the header to the output.

    Can be used for pre-processing or output before the first event
    is written, such as writing a file header.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    return
