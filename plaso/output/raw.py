#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""Returns a PlasoStorage protobuf as a string."""
from plaso.lib import output


class Raw(output.FileProtoLogOutputFormatter):
  """Prints out a "raw" interpretation of the EventObject protobuf."""

  def Usage(self):
    """Return usage information."""
    return ('Returns a raw representation of the EventObject protobuf. '
            'Useful for debugging.')

  def EventBody(self, proto):
    """String representation of an EventObject protobuf.

    Args:
      proto: The EventObject protobuf.

    Returns:
      String representation of an EventObject protobuf.
    """

    out_write = u'%s' % proto
    self.filehandle.write(out_write.encode('utf-8'))
