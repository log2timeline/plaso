# -*- coding: utf-8 -*-
"""This file contains the output module interface classes."""

import abc
import logging

from plaso.lib import errors


class OutputModule(object):
  """Class that implements the output module object interface."""

  NAME = u''
  DESCRIPTION = u''

  def __init__(self, output_mediator):
    """Initializes an output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    super(OutputModule, self).__init__()
    self._output_mediator = output_mediator

  def _ReportEventError(self, event, error_message):
    """Reports an event related error.

    Args:
      event (EventObject): event.
      error_message (str): error message.
    """
    event_identifier = event.GetIdentifier()
    event_identifier_string = event_identifier.CopyToString()
    error_message = (
        u'Event: {0!s} data type: {1:s} display name: {2:s} '
        u'parser chain: {3:s} with error: {4:s}').format(
            event_identifier_string, event.data_type, event.display_name,
            event.parser, error_message)
    logging.error(error_message)

  def Close(self):
    """Closes the output."""
    pass

  def GetMissingArguments(self):
    """Retrieves arguments required by the module that have not been specified.

    Returns:
      list[str]: names of argument that are required by the module and have
          not been specified.
    """
    return []

  def Open(self):
    """Opens the output."""
    pass

  def WriteEvent(self, event):
    """Writes the event to the output.

    Args:
      event (EventObject): event.
    """
    self.WriteEventStart()

    try:
      self.WriteEventBody(event)

    except errors.NoFormatterFound as exception:
      error_message = u'unable to retrieve formatter with error: {0!s}'.format(
          exception)
      self._ReportEventError(event, error_message)

    except errors.WrongFormatter as exception:
      error_message = u'wrong formatter with error: {0!s}'.format(exception)
      self._ReportEventError(event, error_message)

    self.WriteEventEnd()

  @abc.abstractmethod
  def WriteEventBody(self, event):
    """Writes the body of an event to the output.

    Args:
      event (EventObject): event.
    """

  def WriteEventEnd(self):
    """Writes the end of an event to the output.

    Can be used for post-processing or output after an individual event
    has been written, such as writing closing XML tags, etc.
    """
    pass

  def WriteEventMACBGroup(self, event_macb_group):
    """Writes an event MACB group to the output.

    An event MACB group is a group of events that have the same timestamp and
    event data (attributes and values), where the timestamp description (or
    usage) is one or more of MACB (modification, access, change, birth).

    This function is called if the psort engine detected an event MACB group
    so that the output module, if supported, can represent the group as
    such. If not overridden this function will output every event individually.

    Args:
      event_macb_group (list[EventObject]): group of events with identical
          timestamps, attributes and values.
    """
    for event in event_macb_group:
      self.WriteEvent(event)

  def WriteEventStart(self):
    """Writes the start of an event to the output.

    Can be used for pre-processing or output before an individual event
    has been written, such as writing opening XML tags, etc.
    """
    pass

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event
    is written, such as writing a file footer.
    """
    pass

  def WriteHeader(self):
    """Writes the header to the output.

    Can be used for pre-processing or output before the first event
    is written, such as writing a file header.
    """
    pass


class LinearOutputModule(OutputModule):
  """Class that implements a linear output module object."""

  # Need to suppress this since these classes do not implement the
  # abstract method WriteEventBody, classes that inherit from one of these
  # classes need to implement that function.
  # pylint: disable=abstract-method

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.

    Raises:
      ValueError: if the output writer is missing.
    """
    super(LinearOutputModule, self).__init__(output_mediator)
    self._output_writer = None

  def _WriteLine(self, line):
    """Write a single line to the supplied file-like object.

    Args:
      line (str): line of text to write.
    """
    self._output_writer.Write(line)

  def SetOutputWriter(self, output_writer):
    """Set the output writer.

    Args:
      output_writer (CLIOutputWriter): output writer.
    """
    self._output_writer = output_writer

  def Close(self):
    """Closes the output."""
    self._output_writer = None
