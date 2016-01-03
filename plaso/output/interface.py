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
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    super(OutputModule, self).__init__()
    self._output_mediator = output_mediator

  def _GetEventStorageIdentifier(self, event_object):
    """Retrieves the event storage identifier of an event object.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A string containing the event storage identifier or "N/A".
    """
    store_number = getattr(event_object, u'store_number', None)
    store_index = getattr(event_object, u'store_index', None)

    if store_number is None or store_index is None:
      return u'N/A'

    return u'{0:d}:{1:d}'.format(store_number, store_index)

  def Close(self):
    """Closes the output."""
    pass

  def GetMissingArguments(self):
    """Return a list of arguments that are missing from the input.

    Returns:
      A list of argument names that are missing and necessary for the
      module to continue to operate.
    """
    return []

  def Open(self):
    """Opens the output."""
    pass

  def WriteEvent(self, event_object):
    """Writes the event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self.WriteEventStart()

    try:
      self.WriteEventBody(event_object)
    except errors.NoFormatterFound:
      logging.error(
          u'Unable to retrieve formatter for event object: {0:s}:'.format(
              event_object.GetString()))

    self.WriteEventEnd()

  @abc.abstractmethod
  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """

  def WriteEventEnd(self):
    """Writes the end of an event object to the output.

    Can be used for post-processing or output after an individual event object
    has been written, such as writing closing XML tags, etc.
    """
    pass

  def WriteEventStart(self):
    """Writes the start of an event object to the output.

    Can be used for pre-processing or output before an individual event object
    has been written, such as writing opening XML tags, etc.
    """
    pass

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event object
    is written, such as writing a file footer.
    """
    pass

  def WriteHeader(self):
    """Writes the header to the output.

    Can be used for pre-processing or output before the first event object
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
      output_mediator: The output mediator object (instance of OutputMediator).

    Raises:
      ValueError: if the output writer is missing.
    """
    super(LinearOutputModule, self).__init__(output_mediator)
    self._output_writer = None

  def _WriteLine(self, line):
    """Write a single line to the supplied file-like object.

    Args:
      line: the line of text to write.
    """
    self._output_writer.Write(line)

  def SetOutputWriter(self, output_writer):
    """Set the output writer.

    Args:
      output_writer: Optional output writer object (instance of
                     CLIOutputWriter).
    """
    self._output_writer = output_writer

  def Close(self):
    """Closes the output."""
    self._output_writer = None
