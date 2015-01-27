#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
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
"""Represents an EventObject as a string."""

from plaso.output import interface
from plaso.output import manager


class NativePythonOutputFormatter(interface.FileLogOutputFormatter):
  """Prints out a "raw" interpretation of the EventObject."""

  # TODO: Revisit the name of this class, perhaps rename it to
  # something more closely similar to what it is doing now, as in
  # "native" or something else.
  NAME = u'rawpy'
  DESCRIPTION = u'Prints out a "raw" interpretation of the EventObject.'

  def EventBody(self, event_object):
    """Prints out to a filehandle string representation of an EventObject.

    Each EventObject contains both attributes that are considered "reserved"
    and others that aren't. The 'raw' representation of the object makes a
    distinction between these two types as well as extracting the format
    strings from the object.

    Args:
      event_object: The EventObject.
    """
    # TODO: Move the unicode cast into the event object itself, expose
    # a ToString function or something similar that will send back the
    # unicode string.
    self.filehandle.WriteLine(unicode(event_object))


manager.OutputManager.RegisterOutput(NativePythonOutputFormatter)
