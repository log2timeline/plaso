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

from plaso.lib import output
from plaso.serializer import json_serializer


class Json(output.FileLogOutputFormatter):
  """Saves the events into a JSON format."""

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
        json_serializer.JsonEventObjectSerializer.WriteSerialized(event_object))
    self.filehandle.WriteLine(u'\n')
