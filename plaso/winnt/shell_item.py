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
"""This file contains the Windows NT shell item support functions."""

import pyfwsi

from plaso.winnt import shell_folder_ids


if pyfwsi.get_version() < '20140712':
  raise ImportWarning(
      u'Shell item support fuctions require at least pyfwsi 20140712.')


def ShellItemCopyToPath(shell_item):
  """Copies a shell item to a path.

  Args:
    shell_item: the shell item (instance of pyfwsi.item).

  Returns:
    A Unicode string containing the converted shell item path.
  """
  path_segment = None

  if isinstance(shell_item, pyfwsi.root_folder):
    description = shell_folder_ids.DESCRIPTIONS.get(
        shell_item.shell_folder_identifier, None)

    if description:
      path_segment = description
    else:
      path_segment = u'{{{0:s}}}'.format(shell_item.shell_folder_identifier)

  elif isinstance(shell_item, pyfwsi.volume):
    if shell_item.name:
      path_segment = shell_item.name
    elif shell_item.identifier:
      path_segment = u'{{{0:s}}}'.format(shell_item.identifier)

  elif isinstance(shell_item, pyfwsi.file_entry):
    # TODO: create an event?
    # _ = shell_item.get_modification_time_as_integer()

    for exension_block in shell_item.extension_blocks:
      if isinstance(exension_block, pyfwsi.file_entry_extension):
        # TODO: create an event?
        # _ = shell_item.get_creation_time_as_integer()

        # TODO: create an event?
        # _ = shell_item.get_access_time_as_integer()

        path_segment = exension_block.long_name

    if not path_segment and shell_item.name:
      path_segment = shell_item.name

  elif isinstance(shell_item, pyfwsi.network_location):
    if shell_item.location:
      path_segment = shell_item.location

  if path_segment is None and shell_item.class_type == 0x00:
    # TODO: check for signature 0x23febbee
    pass

  if path_segment is None:
    path_segment = u'UNKNOWN: 0x{0:02x}'.format(shell_item.class_type)

  return path_segment


def ShellItemListCopyToPath(shell_item_list):
  """Copies a shell item list to a path.

  Args:
    shell_item_list: the shell item list (instance of pyfwsi.item_list).

  Returns:
    A Unicode string containing the converted shell item list path.
  """
  path_segments_list = []

  for shell_item in shell_item_list.items:
    path_segments_list.append(ShellItemCopyToPath(shell_item))

  return u', '.join(path_segments_list)
