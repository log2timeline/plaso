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

"""Formatter for Hachoir events."""
from plaso.lib import eventdata

__author__ = 'David Nides (david.nides@gmail.com)'


class HachoirFormatter(eventdata.EventFormatter):
  """Formatter for Hachoir based events."""
  DATA_TYPE = 'metadata:hachoir'
  FORMAT_STRING = u'{data}'

  SOURCE_LONG = 'Hachoir Metadata'
  SOURCE_SHORT = 'META'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    event_object.data = u' '.join(
        [u'%s: %s' % (key, value) for (key, value) in sorted(
            event_object.metadata.items())])

    return super(HachoirFormatter, self).GetMessages(event_object)
