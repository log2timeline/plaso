#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the interface for output parsing of plaso.

The default output or storage mechanism of Plaso is not in a human
readable format. There needs to be a way to define the output in such
a way.

After the timeline is collected and stored another tool can read, filter,
sort and process the output inside the storage, and send each processed
entry to an output formatter that takes care of parsing the output into
a human readable format for easy human consumption/analysis.

"""

import abc
import logging
import sys

from plaso.lib import errors
from plaso.lib import registry
from plaso.lib import utils

import pytz


class LogOutputFormatter(object):
  """A base class for formatting output produced by plaso.

  This class exists mostly for documentation purposes. Subclasses should
  override the relevant methods to act on the callbacks.
  """

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

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

  def __init__(self, store, filehandle=sys.stdout, config=None,
               filter_use=None):
    """Constructor for the output module.

    Args:
      store: A StorageFile object that defines the storage.
      filehandle: A file-like object that can be written to.
      config: The configuration object, containing config information.
      filter_use: A filter_interface.FilterObject object.
    """
    zone = getattr(config, 'timezone', 'UTC')
    try:
      self.zone = pytz.timezone(zone)
    except pytz.UnknownTimeZoneError:
      logging.warning(u'Unkown timezone: {0:s} defaulting to: UTC'.format(
          zone))
      self.zone = pytz.utc

    self.filehandle = filehandle
    self.store = store
    self._filter = filter_use
    self._config = config

    self.encoding = getattr(config, 'preferred_encoding', 'utf-8')

  # TODO: this function seems to be only called with the default arguments,
  # so refactor this function away.
  def FetchEntry(self, store_number=-1, store_index=-1):
    """Fetches an entry from the storage.

    Fetches the next entry in the storage file, except if location
    is explicitly indicated.

    Args:
      store_number: The store number if explicit location is to be read.
      store_index: The index into the store, if explicit location is to be
      read.

    Returns:
      An EventObject, either the next one or from a specific location.
    """
    if store_number > 0:
      return self.store.GetEventObject(store_number, store_index)
    else:
      return self.store.GetSortedEntry()

  def WriteEvent(self, evt):
    """Write the output of a single entry to the output filehandle.

    This method takes care of actually outputting each event in
    question. It does so by first prepending it with potential
    start of event, then processes the main body before appending
    a potential end of event.

    Args:
      evt: An EventObject, defined in the event library.
    """
    self.StartEvent()
    self.EventBody(evt)
    self.EndEvent()

  @abc.abstractmethod
  def EventBody(self, evt):
    """Writes the main body of an event to the output filehandle.

    Args:
      evt: An EventObject, defined in the event library.

    Raises:
      NotImplementedError: When not implemented.
    """

  def StartEvent(self):
    """This should be extended by specific implementations.

    This method does all preprocessing or output before each event
    is printed, for instance to surround XML events with tags, etc.
    """
    pass

  def EndEvent(self):
    """This should be extended by specific implementations.

    This method does all the post-processing or output after
    each event has been printed, such as closing XML tags, etc.
    """
    pass

  def Start(self):
    """This should be extended by specific implementations.

    Depending on the file format of the output it may need
    a header. This method should return a header if one is
    defined in that output format.
    """
    pass

  def End(self):
    """This should be extended by specific implementations.

    Depending on the file format of the output it may need
    a footer. This method should return a footer if one is
    defined in that output format.
    """
    pass


# Need to suppress this since these classes do not implement the
# abstract method EventBody, classes that inherit from one of these
# classes need to implement that function.
# pylint: disable=abstract-method
class FileLogOutputFormatter(LogOutputFormatter):
  """A simple file based output formatter."""

  __abstract = True

  def __init__(self, store, filehandle=sys.stdout, config=None,
               filter_use=None):
    """Set up the formatter."""
    super(FileLogOutputFormatter, self).__init__(
        store, filehandle, config, filter_use)
    if isinstance(filehandle, basestring):
      open_filehandle = open(filehandle, 'wb')
    elif hasattr(filehandle, 'write'):
      open_filehandle = filehandle
    else:
      raise IOError(
          u'Unable to determine how to use filehandle passed in: {}'.format(
              type(filehandle)))

    self.filehandle = OutputFilehandle(self.encoding)
    self.filehandle.Open(open_filehandle)

  def End(self):
    """Close the open filehandle after the last output."""
    super(FileLogOutputFormatter, self).End()
    self.filehandle.Close()


class EventBuffer(object):
  """Buffer class for EventObject output processing."""

  MERGE_ATTRIBUTES = ['inode', 'filename', 'display_name']

  def __init__(self, formatter, check_dedups=True):
    """Initialize the EventBuffer.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      formatter: An OutputFormatter object.
      check_dedups: Boolean value indicating whether or not the buffer should
      check and merge duplicate entries or not.
    """
    self._buffer_dict = {}
    self._current_timestamp = 0
    self.duplicate_counter = 0
    self.check_dedups = check_dedups

    self.formatter = formatter
    self.formatter.Start()

  def Append(self, event_object):
    """Append an EventObject into the processing pipeline.

    Args:
      event_object: The EventObject that is being added.
    """
    if not self.check_dedups:
      self.formatter.WriteEvent(event_object)
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
        self.formatter.WriteEvent(event_object)
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

    if self.formatter:
      self.formatter.End()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.End()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


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
    self._filehandle = None
    self._encoding = encoding
    # An attribute stating whether or not this is STDOUT.
    self._standard_out = False

  def Open(self, filehandle=sys.stdout, path=''):
    """Open a filehandle to an output file.

    Args:
      filehandle: A file-like-object that is used to write data to.
      path: If a file like object is not passed in it is possible
      to pass in a path to a file, and a file-like-objec will be created.
    """
    if path:
      self._filehandle = open(path, 'wb')
    else:
      self._filehandle = filehandle

    if not hasattr(self._filehandle, 'name'):
      self._standard_out = True
    elif self._filehandle.name.startswith('<stdout>'):
      self._standard_out = True

  def WriteLine(self, line):
    """Write a single line to the supplied filehandle."""
    if not self._filehandle:
      return

    if self._standard_out:
      # Write using preferred user encoding.
      try:
        self._filehandle.write(line.encode(self._encoding))
      except UnicodeEncodeError:
        logging.error(
            u'Unable to properly write logline, save output to a file to '
            u'prevent missing data.')
        self._filehandle.write(line.encode(self._encoding, 'ignore'))

    else:
      # Write to a file, use unicode.
      self._filehandle.write(line.encode(self.DEFAULT_ENCODING))

  def Close(self):
    """Close the filehandle, if applicable."""
    if self._filehandle and not self._standard_out:
      self._filehandle.close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


def GetOutputFormatter(output_string):
  """Return an output formatter that matches the provided string."""
  # Format the output string (make the input case in-sensitive).
  if type(output_string) not in (str, unicode):
    return None

  format_str = ''.join(
      [output_string[0].upper(), output_string[1:].lower()])
  return LogOutputFormatter.classes.get(format_str, None)


def ListOutputFormatters():
  """Generate a list of all available output formatters."""
  for cl in LogOutputFormatter.classes:
    formatter_class = LogOutputFormatter.classes[cl](None)
    doc_string, _, _ = formatter_class.__doc__.partition('\n')
    yield cl, doc_string
