# -*- coding: utf-8 -*-
"""This file contains the event buffer class."""

import logging

from plaso.lib import errors
from plaso.lib import utils


# TODO: fix docstrings after determining this class is still needed.
class EventBuffer(object):
  """Buffer class for event object output processing.

  Attributes:
    check_dedups: boolean value indicating whether or not the buffer
                  should check and merge duplicate entries or not.
    duplicate_counter: integer that contains the number of duplicates.
  """

  MERGE_ATTRIBUTES = [u'inode', u'filename', u'display_name']

  def __init__(self, output_module, check_dedups=True):
    """Initializes an event buffer object.

    This class is used for buffering up events for duplicate removals
    and for other post-processing/analysis of events before being presented
    by the appropriate output module.

    Args:
      output_module: an output module object (instance of OutputModule).
      check_dedups: optional boolean value indicating whether or not the buffer
                    should check and merge duplicate entries or not.
    """
    self._buffer_dict = {}
    self._current_timestamp = 0
    self._output_module = output_module
    self._output_module.Open()
    self._output_module.WriteHeader()

    self.check_dedups = check_dedups
    self.duplicate_counter = 0

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.End()

  def Append(self, event_object):
    """Append an EventObject into the processing pipeline.

    Args:
      event_object: the EventObject that is being added.
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

  def End(self):
    """Calls the formatter to produce the closing line."""
    self.Flush()

    if self._output_module:
      self._output_module.WriteFooter()
      self._output_module.Close()

  def Flush(self):
    """Flushes the buffer by sending records to a formatter and prints."""
    if not self._buffer_dict:
      return

    for event_object in self._buffer_dict.values():
      try:
        self._output_module.WriteEvent(event_object)
      except errors.WrongFormatter as exception:
        logging.error(u'Unable to write event: {0:s}'.format(exception))

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
      # TODO: remove need for GetUnicodeString.
      val_a = set(utils.GetUnicodeString(
          getattr(event_a, attr, u'')).split(u';'))
      val_b = set(utils.GetUnicodeString(
          getattr(event_b, attr, u'')).split(u';'))
      values_list = list(val_a | val_b)
      values_list.sort() # keeping this consistent across runs helps with diffs
      setattr(event_a, attr, u';'.join(values_list))

    # Special instance if this is a filestat entry we need to combine the
    # description field.
    if getattr(event_a, u'parser', u'') == u'filestat':
      description_a = set(getattr(event_a, u'timestamp_desc', u'').split(u';'))
      description_b = set(getattr(event_b, u'timestamp_desc', u'').split(u';'))
      descriptions = list(description_a | description_b)
      descriptions.sort()
      if event_b.timestamp_desc not in event_a.timestamp_desc:
        setattr(event_a, u'timestamp_desc', u';'.join(descriptions))
