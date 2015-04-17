# -*- coding: utf-8 -*-
"""This file contains the interface for output modules."""

import abc
import logging

from plaso.lib import errors
from plaso.lib import utils


class OutputModule(object):
  """Class that implements the output module object interface."""

  # TODO: refactor this to the cli classes (aka storage helper).
  # Optional arguments to be added to the argument parser.
  # An example would be:
  #   ARGUMENTS = [('--myparameter', {
  #       'action': 'store',
  #       'help': 'This is my parameter help',
  #       'dest': 'myparameter',
  #       'default': '',
  #       'type': 'unicode'})]
  #
  # Where all arguments into the dict object have a direct translation
  # into the argparse parser.
  ARGUMENTS = []

  NAME = u''
  DESCRIPTION = u''

  def __init__(self, output_mediator, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      kwargs: a dictionary of keyword arguments dependending on the output
              module.

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    if kwargs:
      raise ValueError(u'Unused keyword arguments: {0:s}.'.format(
          u', '.join(kwargs.keys())))

    super(OutputModule, self).__init__()
    self._output_mediator = output_mediator

  def Close(self):
    """Closes the output."""
    pass

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

  def __init__(self, output_mediator, output_writer=None, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      output_writer: Optional output writer object (instance of
                     CLIOutputWriter). The default is None.

    Raises:
      ValueError: if the output writer is missing.
    """
    if not output_writer:
      raise ValueError(u'Missing output writer.')

    super(LinearOutputModule, self).__init__(output_mediator, **kwargs)
    self._output_writer = output_writer

  def _WriteLine(self, line):
    """Write a single line to the supplied file-like object.

    Args:
      line: the line of text to write.
    """
    self._output_writer.Write(line)

  def Close(self):
    """Closes the output."""
    self._output_writer = None


class EventBuffer(object):
  """Buffer class for EventObject output processing."""

  MERGE_ATTRIBUTES = [u'inode', u'filename', u'display_name']

  def __init__(self, output_module, check_dedups=True):
    """Initializes an event buffer object.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      output_module: An output module object (instance of OutputModule).
      check_dedups: Optional boolean value indicating whether or not the buffer
                    should check and merge duplicate entries or not.
    """
    self._buffer_dict = {}
    self._current_timestamp = 0
    self._output_module = output_module
    self._output_module.Open()
    self._output_module.WriteHeader()

    self.check_dedups = check_dedups
    self.duplicate_counter = 0

  def Append(self, event_object):
    """Append an EventObject into the processing pipeline.

    Args:
      event_object: The EventObject that is being added.
    """
    if not self.check_dedups:
      self._output_module.WriteEvent(event_object)
      return

    if event_object.timestamp != self._current_timestamp:
      self._current_timestamp = event_object.timestamp
      self.Flush()

    key = event_object.EqualityString()
    if key in self._buffer_dict:
      self.JoinEvents(event_object, self._buffer_dict.pop(key))
    self._buffer_dict[key] = event_object

  def Flush(self):
    """Flushes the buffer by sending records to a formatter and prints."""
    if not self._buffer_dict:
      return

    for event_object in self._buffer_dict.values():
      try:
        self._output_module.WriteEvent(event_object)
      except errors.WrongFormatter as exception:
        logging.error(u'Unable to write event: {:s}'.format(exception))

    self._buffer_dict = {}

  def JoinEvents(self, event_a, event_b):
    """Join this EventObject with another one."""
    self.duplicate_counter += 1
    # TODO: Currently we are using the first event pathspec, perhaps that
    # is not the best approach. There is no need to have all the pathspecs
    # inside the combined event, however which one should be chosen is
    # perhaps something that can be evaluated here (regular TSK in favor of
    # an event stored deep inside a VSS for instance).
    for attr in self.MERGE_ATTRIBUTES:
      val_a = set(utils.GetUnicodeString(getattr(event_a, attr, '')).split(';'))
      val_b = set(utils.GetUnicodeString(getattr(event_b, attr, '')).split(';'))
      values_list = list(val_a | val_b)
      values_list.sort() # keeping this consistent across runs helps with diffs
      setattr(event_a, attr, u';'.join(values_list))

    # Special instance if this is a filestat entry we need to combine the
    # description field.
    if getattr(event_a, 'parser', u'') == 'filestat':
      description_a = set(getattr(event_a, 'timestamp_desc', u'').split(';'))
      description_b = set(getattr(event_b, 'timestamp_desc', u'').split(';'))
      descriptions = list(description_a | description_b)
      descriptions.sort()
      if event_b.timestamp_desc not in event_a.timestamp_desc:
        setattr(event_a, 'timestamp_desc', u';'.join(descriptions))

  def End(self):
    """Call the formatter to produce the closing line."""
    self.Flush()

    if self._output_module:
      self._output_module.WriteFooter()
      self._output_module.Close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.End()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self
