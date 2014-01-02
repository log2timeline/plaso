#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""The SleuthKit helper functions."""

import logging

from plaso.lib import errors


def GetTSKPaths(path_list, tsk_fs):
  """Find the path if it exists.

  Args:
    path_list: A list of either regular expressions or expanded
               paths (strings).
    tsk_fs: The SleuthKit file system object.

  Returns:
    A list of paths.
  """
  paths = []

  for part in path_list:
    if not part:
      continue

    if isinstance(part, basestring):
      if paths:
        for index, path in enumerate(paths):
          paths[index] = u'/'.join([path, part])
      else:
        paths.append(u'/{}'.format(part))
    else:
      found_path = False
      if not paths:
        paths.append('/')

      old_paths = list(paths)
      paths = []
      for real_path in old_paths:
        try:
          tsk_directory = tsk_fs.fs.open_dir(real_path)
        except IOError:
          continue
        for tsk_file in tsk_directory:
          try:
            name = tsk_file.info.name.name
            if not tsk_file.info.meta:
              continue
          except AttributeError as exception:
            logging.error((
                u'[ParseImage] Problem reading file [{0:s}], error: '
                u'{1:s}').format(name, exception))
            continue

          if name == '.' or name == '..':
            continue

          m = part.match(name)
          if m:
            append_path = u'/'.join([real_path, m.group(0)])
            found_path = True
            paths.append(append_path)

      if not found_path:
        raise errors.PathNotFound(u'Path not found inside')

  for real_path in paths:
    yield real_path
