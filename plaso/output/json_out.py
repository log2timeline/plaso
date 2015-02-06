#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""An output module that saves data into a simple JSON format."""

import sys
import json

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
    json_string = json_serializer.JsonEventObjectSerializer.WriteSerialized(
        event_object)

    # unflatten dictionary, for more compact and usable JSON output
    json_dict = json.loads(json_string)
    if 'pathspec' in json_dict and isinstance(json_dict['pathspec'],
        basestring):
      # convert JSON string to a dictionary
      pathspec_dict = json.loads(json_dict['pathspec'])
      # get a reference to the dictionary
      cursor = pathspec_dict
      # iterate through the inner flattened dictionaries
      while 'parent' in cursor and isinstance(cursor['parent'], basestring):
        # convert JSON string to a dict
        cursor['parent'] = json.loads(cursor['parent'])
        # update the reference to point to the inner dictionary
        cursor = cursor['parent']
      # set pathspec member to be the new dictionary
      json_dict['pathspec'] = pathspec_dict

    self.filehandle.WriteLine(
        u'"event_{0:d}": {1:s},\n'.format(
            self._event_counter,
            json.dumps(json_dict)))

    self._event_counter += 1

  def Start(self):
    """Provide a header to the file."""
    self.filehandle.WriteLine(u'{')
    self._event_counter = 0


manager.OutputManager.RegisterOutput(JsonOutputFormatter)
