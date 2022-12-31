# -*- coding: utf-8 -*-
"""Shared functionality for text file based output modules."""

import abc
import heapq
import os

from plaso.output import interface


class SortedStringHeap(object):
  """Heap to sort output strings."""

  _MAXIMUM_NUMBER_OF_STRINGS = 100000

  def __init__(self):
    """Initializes a heap."""
    super(SortedStringHeap, self).__init__()
    self._heap = []

  def IsFull(self):
    """Determines if the heap is full.

    Returns:
      bool: True if the heap is full.
    """
    return len(self._heap) >= self._MAXIMUM_NUMBER_OF_STRINGS

  def PopString(self):
    """Pops a string from the heap.

    Returns:
      str: string.
    """
    try:
      _, string = heapq.heappop(self._heap)
    except IndexError:
      return None

    return string

  def PopStrings(self):
    """Pops strings from the heap.

    Yields:
      str: string.
    """
    string = self.PopString()
    while string:
      yield string
      string = self.PopString()

  def PushString(self, sort_key, string):
    """Pushes a string onto the heap.

    Args:
      sort_key (str): key for the sort order.
      string (str): string.
    """
    heapq.heappush(self._heap, (sort_key, string))


class TextFileOutputModule(interface.OutputModule):
  """Shared functionality of an output module that writes to a text file."""

  WRITES_OUTPUT_FILE = True

  _ENCODING = 'utf-8'

  def __init__(self):
    """Initializes an output module that writes to a text file."""
    super(TextFileOutputModule, self).__init__()
    self._file_object = None

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


class SortedTextFileOutputModule(TextFileOutputModule):
  """Shared functionality of an output module that writes to a text file."""

  _SORT_KEY_FIELD_NAMES = []

  def __init__(self, event_formatting_helper):
    """Initializes an output module that writes to a text file.

    Args:
      event_formatting_helper (EventFormattingHelper): event formatting helper.
    """
    super(SortedTextFileOutputModule, self).__init__()
    self._event_formatting_helper = event_formatting_helper
    self._last_sort_key = None
    self._sorted_strings_heap = SortedStringHeap()

  def _FlushSortedStringsHeap(self):
    """Flushed the sorted strings heap."""
    for output_text in self._sorted_strings_heap.PopStrings():
      self.WriteText(output_text)

    self._last_sort_key = None

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
    return self._event_formatting_helper.GetFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

  @abc.abstractmethod
  def _GetString(self, output_mediator, field_values):
    """Retrieves an output string.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.

    Returns:
      str: output string.
    """

  def _WriteFieldValues(self, output_mediator, field_values):
    """Writes field values to the output.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfVFS.
      field_values (dict[str, str]): output field values per name.
    """
    output_text = self._GetString(output_mediator, field_values)
    if output_text:
      sort_key = ' '.join([
          field_values.get(field_name) or ''
          for field_name in self._SORT_KEY_FIELD_NAMES])
      self._sorted_strings_heap.PushString(sort_key, output_text)

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
    sort_key = event.timestamp
    if self._last_sort_key is None:
      self._last_sort_key = sort_key

    if sort_key != self._last_sort_key or self._sorted_strings_heap.IsFull():
      self._FlushSortedStringsHeap()

    super(SortedTextFileOutputModule, self).WriteFieldValues(
        output_mediator, event, event_data, event_data_stream, event_tag)

  def WriteFooter(self):
    """Writes the footer to the output.

    Can be used for post-processing or output after the last event
    is written, such as writing a file footer.
    """
    self._FlushSortedStringsHeap()
