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
"""Contains helper functions for output modules."""
import re

# Few regular expressions.
# TODO: Remove these regular expressions in favor of a more clearly defined
# ontology that strictly enforces certain keywords, perhaps changing the field
# to an enum.
MODIFIED_RE = re.compile(r'modif', re.I)
ACCESS_RE = re.compile(r'visit', re.I)
CREATE_RE = re.compile(r'(create|written)', re.I)


def GetLegacy(evt):
  """Return a legacy MACB representation of the event."""
  # TODO: Fix this function when the MFT parser has been implemented.
  # The filestat parser is somewhat limited.
  # Also fix this when duplicate entries have been implemented so that
  # the function actually returns more than a single entry (as in combined).
  if evt.data_type.startswith('fs:'):
    letter = evt.timestamp_desc[0]

    if letter == 'm':
      return 'M...'
    elif letter == 'a':
      return '.A..'
    elif letter == 'c':
      if evt.timestamp_desc[1] == 'r':
        return '...B'

      return '..C.'
    else:
      return '....'

  letters = []
  m = MODIFIED_RE.search(evt.timestamp_desc)

  if m:
    letters.append('M')
  else:
    letters.append('.')

  m = ACCESS_RE.search(evt.timestamp_desc)

  if m:
    letters.append('A')
  else:
    letters.append('.')

  m = CREATE_RE.search(evt.timestamp_desc)

  if m:
    letters.append('C')
  else:
    letters.append('.')

  letters.append('.')

  return ''.join(letters)


def GetUsernameFromPreProcess(pre_obj, id_value):
  """Return a username from a preprocessing object and SID/UID if defined.

  Args:
    pre_obj: The PlasoPreprocess object that contains preprocessing information
             for the store that this EventObject comes from.
    id_value: This could be either a UID or a SID and should match the
              appropriate UID or SID value that is stored inside the
              PlasoPreprocess object.

  Returns:
    If a username is found within the PlasoPreprocess object it is returned,
    otherwise the string '-' is returned back.
  """
  if not pre_obj:
    return '-'

  if not id_value:
    return '-'

  if hasattr(pre_obj, 'users'):
    for user in pre_obj.users:
      if user.get('sid', '') == id_value:
        return user.get('name', '-')
      if user.get('uid', '') == id_value:
        return user.get('name', '-')

  return '-'


def BuildHostDict(storage_object):
  """Return a dict object from a PlasoStorage object.

  Build a dict object based on the PlasoPreprocess objects stored inside
  a storage file.

  Args:
    storage_object: The PlasoStorage object that stores all the EventObjects.

  Returns:
    A dict object that has the store number as a key and the hostname
    as the value to that key.
  """
  host_dict = {}
  if not storage_object:
    return host_dict

  for info in storage_object.GetStorageInformation():
    if hasattr(info, 'store_range') and hasattr(info, 'hostname'):
      for store_number in range(info.store_range[0], info.store_range[1]):
        # TODO: A bit wasteful, if the range is large we are wasting keys.
        # Rewrite this logic into a more optimal one.
        host_dict[store_number] = info.hostname

  return host_dict
