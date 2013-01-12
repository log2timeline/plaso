#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""A place to store information about events, such as format strings, etc."""

import re

from plaso.lib import errors
from plaso.lib import registry
from plaso.lib import storage


class PlasoFormatter(object):
  """A formatter class that defines a format string for an event type."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('None', re.DOTALL)

  # The format string.
  FORMAT_STRING = u''
  FORMAT_STRING_SHORT = u''

  def __init__(self, event_object):
    """Set up the formatter and determine if this is the right formatter."""
    self.extra_attributes = {}
    # Check if it is a protobuf or a regular python object.
    if hasattr(event_object, 'attributes') and hasattr(
        event_object.attributes, 'MergeFrom'):
      self.base_attributes = dict(
          storage.GetAttributeValue(a) for a in event_object.attributes)
      for attr, value in event_object.ListFields():
        # Don't want to include attributes that are themselves a message.
        if attr.type != 11:
          self.extra_attributes[attr.name] = value
    else:
      self.base_attributes = event_object.attributes

    self.parser = self.base_attributes.get('parser', None)
    source = getattr(event_object, 'source_long', 'NO SOURCE')
    time_desc = getattr(event_object, 'timestamp_desc', 'NO TIMEDESC')
    self.signature = u'%s:%s:%s' % (self.parser, source, time_desc)

    if not self.ID_RE.match(self.signature):
      raise errors.WrongFormatter('Unable to handle this file type.')

    self.event_object = event_object

    # Extend the basic attribute dict with other fields/attributes too.
    self.extra_attributes.update(self.base_attributes)

    self.format_string = self.FORMAT_STRING
    self.format_string_short = self.FORMAT_STRING_SHORT

  def GetMessages(self):
    """Return a list of messages extracted from an EventObject.

    The l2t_csv and other formats are dependent on a message field,
    referred to as description_long and description_short in l2t_csv.

    Plaso does not store this field explicitly, it only contains a format
    string and the appropriate attributes.

    This method takes the format string and converts that back into a
    formatted string that can be used for display.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    try:
      msg = self.format_string.format(**self.extra_attributes)
    except KeyError as e:
      msgs = []
      msgs.append(u'Error in format string [%s]' % e)
      msgs.append(u'<%s>' % self.format_string)
      for attr, value in self.base_attributes.items():
        msgs.append(u'{0}: {1}'.format(attr, value))

      msg = u' '.join(msgs)

    # Adjust the message string.
    msg = msg.replace('\r', '').replace('\n', '')

    if self.format_string_short:
      try:
        msg_short = self.format_string_short.format(
            **self.extra_attributes).replace('\r', '').replace('\n', '')
      except KeyError:
        msg_short = (
            u'Unable to format string: %s') % self.format_string_short
    else:
      if len(msg) > 80:
        msg_short = u'%s...' % msg[0:77]
      else:
        msg_short = msg

    return msg, msg_short


class TextFormatter(PlasoFormatter):
  """A simple implementation of a text based formatter."""
  __abstract = True

  FORMAT_STRING = u'{body}'


class RegistryFormatter(PlasoFormatter):
  """A simple implementation of a text based formatter."""
  __abstract = True

  FORMAT_STRING = u'[{keyname}] {text}'
  FORMAT_STRING_ALTERNATIVE = u'{text}'


def GetFormatter(event_object):
  """A simple helper to return the formatter for a given EventObject."""
  for cl in PlasoFormatter.classes:
    try:
      formatter = PlasoFormatter.classes[cl](event_object)
      return formatter
    except errors.WrongFormatter:
      pass


def GetMessageStrings(event_object):
  """A simple helper that returns message strings from a given event object."""
  formatter = GetFormatter(event_object)

  if not formatter:
    return u'', u''

  return formatter.GetMessages()
