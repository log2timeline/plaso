#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
import StringIO
import sys

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

  def __init__(self, store, filehandle=sys.stdout, zone=pytz.utc):
    """Constructor for the output module.

    Args:
      store: A PlasoStorage object that defines the storage.
      filehandle: A file-like object that can be written to.
      zone: The output time zone (a pytz object).
    """
    self.zone = zone
    self.filehandle = filehandle
    self.store = store

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
      return self.store.GetEntry(store_number, store_index)
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

  def EventBody(self, evt):
    """Writes the main body of an event to the output filehandle.

    Args:
      evt: An EventObject, defined in the event library.

    Raises:
      NotImplementedError: When not implemented.
    """
    raise NotImplementedError

  def StartEvent(self):
    """This should be extended by specific implementations.

    This method does all pre-processing or output before each event
    is printed, for instance to surround XML events with tags, etc.
    """
    self.filehandle.write('')

  def EndEvent(self):
    """This should be extended by specific implementations.

    This method does all the post-processing or output after
    each event has been printed, such as closing XML tags, etc.
    """
    self.filehandle.write('')

  def Start(self):
    """This should be extended by specific implementations.

    Depending on the file format of the output it may need
    a header. This method should return a header if one is
    defined in that output format.
    """
    self.filehandle.write('')

  def End(self):
    """This should be extended by specific implementations.

    Depending on the file format of the output it may need
    a footer. This method should return a footer if one is
    defined in that output format.
    """
    self.filehandle.write('')

  def Usage(self):
    """Return a quick help message that describes the output provided."""
    return 'This is a generic output module that provides no context.'


class FileLogOutputFormatter(LogOutputFormatter):
  """A simple file based output formatter."""

  __abstract = True

  def __init__(self, store, filehandle=sys.stdout, zone=pytz.utc):
    """Set up the formatter."""
    super(FileLogOutputFormatter, self).__init__(store, filehandle, zone)
    if not isinstance(filehandle, (file, StringIO.StringIO)):
      self.filehandle = open(filehandle, 'w')

  def End(self):
    """Close the open filehandle after the last output."""
    super(FileLogOutputFormatter, self).End()
    self.filehandle.close()


class ProtoLogOutputFormatter(LogOutputFormatter):
  """A simple formatter that processes EventObject protobufs."""
  __abstract = True

  def FetchEntry(self, store_number=-1, store_index=-1):
    """Fetches an entry from the storage."""
    if store_index > 0:
      return self.store.GetProtoEntry(store_number, store_index)
    else:
      return self.store.GetSortedEntry(True)


class FileProtoLogOutputFormatter(FileLogOutputFormatter):
  """A sipmle file based output formatter that processes raw protobufs."""
  __abstract = True

  def FetchEntry(self, store_number=-1, store_index=-1):
    """Fetches an entry from the storage."""
    if store_index > 0:
      return self.store.GetProtoEntry(store_number, store_index)
    else:
      return self.store.GetSortedEntry(True)


class EventBuffer(object):
  """Buffer class for EventObject output processing."""

  def __init__(self, formatter, check_dedups=True):
    """Initalizes the EventBuffer.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      formatter: An OutputFormatter object.
      check_dedups: Boolean value indicating whether or not the buffer should
      check and merge duplicate entries or not.
    """
    self._buffer_list = []
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
    if event_object.timestamp != self._current_timestamp:
      self._current_timestamp = event_object.timestamp
      self.Flush()

    self._buffer_list.append(event_object)

  def Flush(self):
    """Flushes the buffer by sending records to a formatter and prints."""
    if not self._buffer_list:
      return

    if len(self._buffer_list) == 1:
      self.formatter.WriteEvent(self._buffer_list.pop())
    elif not self.check_dedups:
      for event_object in self._buffer_list:
        self.formatter.WriteEvent(event_object)
    else:
      length = len(self._buffer_list)
      for index in range(0, length):
        event_object = self._buffer_list[index]
        if not event_object:
          continue
        for in_index in range(index + 1, length):
          event_compare = self._buffer_list[in_index]
          if not event_compare:
            continue
          if event_object == event_compare:
            self.JoinEvents(event_object, event_compare)
            self._buffer_list[in_index] = None

        # Comparison done, objects combined, time to write it to output.
        self.formatter.WriteEvent(event_object)

    self._buffer_list = []

  def JoinEvents(self, event_a, event_b):
    """Join this EventObject with another one."""
    self.duplicate_counter += 1
    # TODO: Currently we are using the first event pathspec, perhaps that
    # is not the best approach. There is no need to have all the pathspecs
    # inside the combined event, however which one should be chosen is
    # perhaps something that can be evaluated here (regular TSK in favor of
    # an event stored deep inside a VSS for instance).
    event_a.inode = ';'.join([
      utils.GetUnicodeString(getattr(event_a, 'inode', '')),
      utils.GetUnicodeString(getattr(event_b, 'inode', ''))])
    event_a.filename= ';'.join([
      utils.GetUnicodeString(getattr(event_a, 'filename', '')),
      utils.GetUnicodeString(getattr(event_b, 'filename', ''))])
    event_a.display_name= ';'.join([
      utils.GetUnicodeString(getattr(event_a, 'display_name', '')),
      utils.GetUnicodeString(getattr(event_b, 'display_name', ''))])

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
    yield cl, LogOutputFormatter.classes[cl](None).Usage()
