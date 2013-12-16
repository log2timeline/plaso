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
"""File for PyVFS migration to contain all TSK specific preprocess code."""

import logging
import re

from plaso.lib import errors
from plaso.lib import pfile
from plaso.lib import preprocess
from plaso.lib import putils

import pytsk3


class TSKFileCollector(preprocess.Collector):
  """A wrapper around collecting files from TSK images."""

  def __init__(self, pre_obj, image_path, offset=0):
    """Set up the TSK file collector."""
    super(TSKFileCollector, self).__init__(pre_obj)
    self._image_path = image_path
    self._image_offset = offset
    self._fscache = pfile.FilesystemCache()
    self._fs_obj = self._fscache.Open(image_path, offset)

  def GetPaths(self, path_list):
    """Return a path."""
    paths = []

    for part in path_list:
      if not part:
        continue

      if isinstance(part, (str, unicode)):
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
            directory = self._fs_obj.fs.open_dir(real_path)
          except IOError as e:
            continue
          for f in directory:
            try:
              name = f.info.name.name
              if not f.info.meta:
                continue
            except AttributeError as e:
              logging.error('[ParseImage] Problem reading file [%s], error: %s',
                            name, e)
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

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern."""
    ret = []
    file_re = re.compile(r'^%s$' % file_name, re.I | re.S)
    try:
      directory = self._fs_obj.fs.open_dir(path)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open directory: %s [%s]' % (path, e))

    for tsk_file in directory:
      try:
        f_type = tsk_file.info.meta.type
        name = tsk_file.info.name.name
      except AttributeError:
        continue
      if f_type == pytsk3.TSK_FS_META_TYPE_REG:
        m = file_re.match(name)
        if m:
          ret.append(u'%s/%s' % (path, name))

    return ret

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return putils.OpenTskFile(
        path, self._image_path, int(self._image_offset / 512), self._fscache)


class VSSFileCollector(TSKFileCollector):
  """A wrapper around collecting files from a VSS store from an image file."""

  def __init__(self, pre_obj, image_path, store_nr, offset=0):
    """Constructor for the VSS File collector."""
    super(VSSFileCollector, self).__init__(pre_obj, image_path, offset)
    self._store_nr = store_nr
    self._fscache = pfile.FilesystemCache()
    self._fs_obj = self._fscache.Open(
        image_path, offset, store_nr)

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return putils.OpenVssFile(path, self._image_path, self._store_nr,
                              int(self._image_offset / 512), self._fscache)
