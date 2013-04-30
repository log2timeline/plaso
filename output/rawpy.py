#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Represents an EventObject as a string."""
from plaso.lib import output


class Rawpy(output.FileLogOutputFormatter):
  """Prints out a "raw" interpretation of the EventObject."""
  # TODO: Revisit the name of this class, perhaps rename it to
  # something more closely similar to what it is doing now, as in
  # "native" or something else.

  def Usage(self):
    """Return usage information."""
    return ('Returns a raw representation of the EventObject. Useful for'
            ' debugging.')

  def EventBody(self, event_object):
    """Prints out to a filehandle string representation of an EventObject.

    Each EventObject contains both attributes that are considered "reserved"
    and others that aren't. The 'raw' representation of the object makes a
    distinction between these two types as well as extracting the format
    strings from the object.

    Args:
      event_object: The EventObject.
    """
    out_write = u'%s' % event_object
    self.filehandle.write(out_write.encode('utf-8'))
