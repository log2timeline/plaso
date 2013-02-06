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
import pprint

from plaso.lib import eventdata
from plaso.lib import output
from plaso.lib import utils


class Rawpy(output.FileLogOutputFormatter):
  """Prints out a "raw" interpretation of the EventObject."""
  # TODO: Revisit the name of this class, perhaps rename it to
  # something more closely similar to what it is doing now, as in
  # "native" or something else.

  def Start(self):
    """Set up the pretty printer."""
    self.printer = pprint.PrettyPrinter(indent=8)

  def Usage(self):
    """Return usage information."""
    return ('Returns a raw representation of the EventObject. Useful for'
            ' debugging.')

  def EventBody(self, evt):
    """Prints out to a filehandle string representation of an EventObject.

    Each EventObject contains both attributes that are considered "reserved"
    and others that aren't. The 'raw' representation of the object makes a
    distinction between these two types as well as extracting the format
    strings from the object.

    Args:
      evt: The EventObject.
    """

    out_write = []
    out_reserved = []
    out_reserved.append('+-' * 80)
    out_reserved.append('[Reserved attributes]:')
    out_write.append('[Additional attributes]:')

    for attr_key, attr_value in sorted(evt.GetValues().items()):
      if attr_key in utils.RESERVED_VARIABLES:
        if attr_key == 'pathspec':
          out_reserved.append(u'  {{{0}}}\n{2}\n{1}{2}'.format(
              attr_key, attr_value.ToProto(), '-' * 30))
        else:
          out_reserved.append(u'  {{{key}}} {value}'.format(
                key=attr_key, value=self.printer.pformat(attr_value)))
      else:
        out_write.append(u'  {{{key}}} {value}'.format(
              key=attr_key, value=self.printer.pformat(attr_value)))
    out_write.append('')
    out_reserved.append('')
    out_reserved.append('')

    self.filehandle.write('\n'.join(out_reserved).encode('utf-8'))
    self.filehandle.write('\n'.join(out_write).encode('utf-8'))
    self.filehandle.write('\n[Message strings]:\n')
    event_formatter = eventdata.EventFormatterManager.GetFormatter(evt)
    if not event_formatter:
      self.filehandle.write('None')
    else:
      msg, msg_short = event_formatter.GetMessages(evt)
      self.filehandle.write(u'{2:>7}: {0}\n{3:>7}: {1}\n\n'.format(
          msg_short, msg, 'Short', 'Long'))
