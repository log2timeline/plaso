# -*- coding: utf-8 -*-
"""This file contains the output module interface classes."""

import abc
import os

from plaso.lib import errors
from plaso.output import logger


class OutputModule(object):
  """Output module interface."""

  NAME = ''
  DESCRIPTION = ''

  # Value to indicate the output module writes to an output file.
  WRITES_OUTPUT_FILE = False

  def __init__(self, output_mediator):
    """Initializes an output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
    """
    super(OutputModule, self).__init__()
    self._output_mediator = output_mediator

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

  def WriteEvent(self, event, event_data, event_data_stream, event_tag):
    """Writes the event to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    try:
      self.WriteEventBody(event, event_data, event_data_stream, event_tag)

    except errors.NoFormatterFound as exception:
      error_message = 'unable to retrieve formatter with error: {0!s}'.format(
          exception)
      self._ReportEventError(event, event_data, error_message)

    except errors.WrongFormatter as exception:
      error_message = 'wrong formatter with error: {0!s}'.format(exception)
      self._ReportEventError(event, event_data, error_message)

  @abc.abstractmethod
  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """

  def WriteEventMACBGroup(self, event_macb_group):
    """Writes an event MACB group to the output.

    An event MACB group is a group of events that have the same timestamp and
    event data (attributes and values), where the timestamp description (or
    usage) is one or more of MACB (modification, access, change, birth).

    This function is called if the psort engine detected an event MACB group
    so that the output module, if supported, can represent the group as
    such. If not overridden this function will output every event individually.

    Args:
      event_macb_group (list[tuple[EventObject, EventData, EventDataStream,
          EventTag]]): group of events with identical timestamps, attributes
          and values.
    """
    for event, event_data, event_data_stream, event_tag in event_macb_group:
      self.WriteEvent(event, event_data, event_data_stream, event_tag)

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event
    is written, such as writing a file footer.
    """
    return

  def WriteHeader(self):
    """Writes the header to the output.

    Can be used for pre-processing or output before the first event
    is written, such as writing a file header.
    """
    return


class TextFileOutputModule(OutputModule):
  """Shared functionality of an output module that writes to a text file."""

  WRITES_OUTPUT_FILE = True

  _ENCODING = 'utf-8'

  def __init__(self, output_mediator, event_formatting_helper):
    """Initializes an output module that writes to a text file.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
      event_formatting_helper (EevntFormattingHelper): event formatting helper.
    """
    super(TextFileOutputModule, self).__init__(output_mediator)
    self._event_formatting_helper = event_formatting_helper
    self._file_object = None

  def Close(self):
    """Closes the output file."""
    if self._file_object:
      self._file_object.close()
      self._file_object = None

  def Open(self, path=None, **kwargs):  # pylint: disable=arguments-differ
    """Opens the output file.

    Args:
      path (Optional[str]): path of the output file.

    Raises:
      IOError: if the specified output file already exists.
      OSError: if the specified output file already exists.
      ValueError: if path is not set.
    """
    if not path:
      raise ValueError('Missing path.')

    if os.path.isfile(path):
      raise IOError((
          'Unable to use an already existing file for output '
          '[{0:s}]').format(path))

    self._file_object = open(path, 'wt', encoding=self._ENCODING)  # pylint: disable=consider-using-with

  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    output_text = self._event_formatting_helper.GetFormattedEvent(
        event, event_data, event_data_stream, event_tag)

    self.WriteLine(output_text)

  def WriteLine(self, text):
    """Writes a line of text to the output file.

    Args:
      text (str): text to output.
    """
    self._file_object.write('{0:s}\n'.format(text))

  def WriteText(self, text):
    """Writes text to the output file.

    Args:
      text (str): text to output.
    """
    self._file_object.write(text)
