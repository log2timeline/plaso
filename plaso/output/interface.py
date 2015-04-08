# -*- coding: utf-8 -*-
"""This file contains the interface for output modules."""

import abc
import logging
import sys

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


# Need to suppress this since these classes do not implement the
# abstract method WriteEventBody, classes that inherit from one of these
# classes need to implement that function.
# pylint: disable=abstract-method
class FileOutputModule(OutputModule):
  """A file-based output module."""

  def __init__(self, output_mediator, filehandle=sys.stdout, **kwargs):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
    """
    super(FileOutputModule, self).__init__(output_mediator, **kwargs)

    if isinstance(filehandle, basestring):
      open_file_object = open(filehandle, 'wb')

    # Check if the filehandle object has a write method.
    elif hasattr(filehandle, u'write'):
      open_file_object = filehandle

    else:
      raise ValueError(u'Unsupported file handle.')

    self._file_object = OutputFilehandle(self._output_mediator.encoding)
    self._file_object.Open(open_file_object)

  def _WriteLine(self, line):
    """Write a single line to the supplied file-like object.

    Args:
      line: the line of text to write.
    """
    self._file_object.WriteLine(line)

  def Close(self):
    """Closes the output."""
    self._file_object.Close()


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


# TODO: replace by output writer.
class OutputFilehandle(object):
  """A simple wrapper for filehandles to make character encoding easier.

  All data is stored as an unicode text internally. However there are some
  issues with clients that try to output unicode text to a non-unicode terminal.
  Therefore a wrapper is created that checks if we are writing to a file, thus
  using the default unicode encoding or if the attempt is to write to the
  terminal, for which the default encoding of that terminal is used to encode
  the text (if possible).
  """

  DEFAULT_ENCODING = 'utf-8'

  def __init__(self, encoding='utf-8'):
    """Initialize the output file handler.

    Args:
      encoding: The default terminal encoding, only used if attempted to write
                to the terminal.
    """
    super(OutputFilehandle, self).__init__()
    self._encoding = encoding
    self._file_object = None
    # An attribute stating whether or not this is STDOUT.
    self._standard_out = False

  def Open(self, filehandle=sys.stdout, path=''):
    """Open a filehandle to an output file.

    Args:
      filehandle: A file-like object that is used to write data to.
      path: If a file like object is not passed in it is possible
            to pass in a path to a file, and a file-like object will be created.
    """
    if path:
      self._file_object = open(path, 'wb')
    else:
      self._file_object = filehandle

    if not hasattr(self._file_object, 'name'):
      self._standard_out = True
    elif self._file_object.name.startswith('<stdout>'):
      self._standard_out = True

  def WriteLine(self, line):
    """Write a single line to the supplied filehandle.

    Args:
      line: the line of text to write.
    """
    if not self._file_object:
      return

    if self._standard_out:
      # Write using preferred user encoding.
      try:
        self._file_object.write(line.encode(self._encoding))
      except UnicodeEncodeError:
        logging.error(
            u'Unable to properly write logline, save output to a file to '
            u'prevent missing data.')
        self._file_object.write(line.encode(self._encoding, 'ignore'))

    else:
      # Write to a file, use unicode.
      self._file_object.write(line.encode(self.DEFAULT_ENCODING))

  def Close(self):
    """Close the filehandle, if applicable."""
    if self._file_object and not self._standard_out:
      self._file_object.close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self
