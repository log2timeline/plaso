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
"""Contains helper functions for output modules."""
import re

from plaso.proto import plaso_storage_pb2

# Few regular expressions.
MODIFIED_RE = re.compile(r'modif', re.I)
ACCESS_RE = re.compile(r'visit', re.I)
CREATE_RE = re.compile(r'(create|written)', re.I)

RESERVED_VARIABLES = frozenset(
    ['username', 'inode', 'hostname', 'body', 'parser', 'regvalue'])


def GetLegacy(event_proto):
  """Return a legacy MACB representation of the event."""
  # TODO: Fix this function when the MFT parser has been implemented.
  # The filestat parser is somewhat limited.
  # Also fix this when duplicate entries have been implemented so that
  # the function actually returns more than a single entry (as in combined).
  if event_proto.source_short == plaso_storage_pb2.EventObject.FILE:
    letter = event_proto.timestamp_desc[0]

    if letter == 'm':
      return 'M...'
    elif letter == 'a':
      return '.A..'
    elif letter == 'c':
      return '..C.'
    else:
      return '....'

  letters = []
  m = MODIFIED_RE.search(event_proto.timestamp_desc)

  if m:
    letters.append('M')
  else:
    letters.append('.')

  m = ACCESS_RE.search(event_proto.timestamp_desc)

  if m:
    letters.append('A')
  else:
    letters.append('.')

  m = CREATE_RE.search(event_proto.timestamp_desc)

  if m:
    letters.append('C')
  else:
    letters.append('.')

  letters.append('.')

  return ''.join(letters)

