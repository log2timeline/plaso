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
"""Formatter for Windows NT Registry (REGF) files."""
from plaso.lib import eventdata


class WinRegistryGenericFormatter(eventdata.EventFormatter):
  """Formatter for a generic Windows Registry key or value."""
  DATA_TYPE = 'windows:registry:key_value'

  FORMAT_STRING = u'[{keyname}] {text}'
  FORMAT_STRING_ALTERNATIVE = u'{text}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    regvalue = getattr(event_object, 'regvalue', {})
    text = u' '.join([u'%s: %s' % (key, value) for (key, value)
                      in sorted(regvalue.items())])

    event_object.text = text
    if hasattr(event_object, 'keyname'):
      self.format_string = self.FORMAT_STRING
    else:
      self.format_string = self.FORMAT_STRING_ALTERNATIVE

    return super(WinRegistryGenericFormatter, self).GetMessages(event_object)

  def GetSources(self, event_object):
    """Returns a list of source short and long messages for the event."""
    self.source_string = getattr(
        event_object, 'source_long', u'{} key'.format(
            getattr(event_object, 'registry_type', 'UNKNOWN')))
    if hasattr(event_object, 'source_append'):
      self.source_string += u'%s' % event_object.source_append

    return super(WinRegistryGenericFormatter, self).GetSources(event_object)
