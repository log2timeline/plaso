# -*- coding: utf-8 -*-
"""An output module that saves data into a JSON format."""

import sys

from plaso.output import interface
from plaso.output import manager
from plaso.serializer import json_serializer


class JsonOutputFormatter(interface.FileOutputModule):
  """Output module for the JSON format."""

  NAME = u'json'
  DESCRIPTION = u'Saves the events into a JSON format.'

  def __init__(
      self, store, formatter_mediator, filehandle=sys.stdout, config=None,
      filter_use=None):
    """Initializes the output module object.

    Args:
      store: A storage file object (instance of StorageFile) that defines
             the storage.
      formatter_mediator: The formatter mediator object (instance of
                          FormatterMediator).
      filehandle: Optional file-like object that can be written to.
                  The default is sys.stdout.
      config: Optional configuration object, containing config information.
              The default is None.
      filter_use: Optional filter object (instance of FilterObject).
                  The default is None.
    """
    super(JsonOutputFormatter, self).__init__(
        store, formatter_mediator, filehandle=filehandle, config=config,
        filter_use=filter_use)
    self._event_counter = 0

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._WriteLine(u'"event_{0:d}": {1:s},\n'.format(
        self._event_counter,
        json_serializer.JsonEventObjectSerializer.WriteSerialized(
            event_object)))

    self._event_counter += 1

  def WriteFooter(self):
    """Writes the footer to the output."""
    # Adding a label for "event_foo" due to JSON expecting a label
    # after a comma. The only way to provide that is to either know
    # what the last event is going to be (which we don't) or to add
    # a dummy event in the end that has no data in it.
    self._WriteLine(u'"event_foo": "{}"}')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(u'{')
    self._event_counter = 0


manager.OutputManager.RegisterOutput(JsonOutputFormatter)
