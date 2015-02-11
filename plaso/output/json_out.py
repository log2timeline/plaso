# -*- coding: utf-8 -*-
"""An output module that saves data into a simple JSON format."""

import sys

from plaso.output import interface
from plaso.output import manager
from plaso.serializer import json_serializer


class JsonOutputFormatter(interface.FileLogOutputFormatter):
  """Defines the JSON output formatter class."""

  NAME = u'json'
  DESCRIPTION = u'Saves the events into a JSON format.'

  def __init__(self, store, filehandle=sys.stdout, config=None,
               filter_use=None):
    """Constructor for the output module.

    Args:
      store: A StorageFile object that defines the storage.
      filehandle: A file-like object that can be written to.
      config: The configuration object, containing config information.
      filter_use: A filter_interface.FilterObject object.
    """
    super(JsonOutputFormatter, self).__init__(
        store, filehandle, config, filter_use)
    self._event_counter = 0

  def End(self):
    """Provide a footer."""
    # Adding a label for "event_foo" due to JSON expecting a label
    # after a comma. The only way to provide that is to either know
    # what the last event is going to be (which we don't) or to add
    # a dummy event in the end that has no data in it.
    self.filehandle.WriteLine(u'"event_foo": "{}"}')
    super(JsonOutputFormatter, self).End()

  def EventBody(self, event_object):
    """Prints out to a filehandle string representation of an EventObject.

    Each event object contains both attributes that are considered "reserved"
    and others that aren't. The 'raw' representation of the object makes a
    distinction between these two types as well as extracting the format
    strings from the object.

    Args:
      event_object: The event object (instance of EventObject).
    """
    self.filehandle.WriteLine(
        u'"event_{0:d}": {1:s},\n'.format(
            self._event_counter,
            json_serializer.JsonEventObjectSerializer.WriteSerialized(
                event_object)))

    self._event_counter += 1

  def Start(self):
    """Provide a header to the file."""
    self.filehandle.WriteLine(u'{')
    self._event_counter = 0


manager.OutputManager.RegisterOutput(JsonOutputFormatter)
