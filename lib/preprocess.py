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
"""This file contains classes used for preprocessing in plaso."""
import abc
import logging
import os
import re

from plaso.lib import errors
from plaso.lib import lexer
from plaso.lib import pfile
from plaso.lib import putils
from plaso.lib import registry
from plaso.lib import win_registry


class PreprocessPlugin(object):
  """A preprocessing class defining a single attribute.

  Any pre-processing plugin that implements this interface
  should define which operating system this plugin supports.

  The OS variable supports the following values:
    + Windows
    + Linux
    + MacOSX

  Since some plugins may require knowledge gained from
  other checks all plugins have a weight associated to it.
  The weight variable can have values from one to three:
    + 1 - Requires no prior knowledge, can run immediately.
    + 2 - Requires knowledge from plugins with weight 1.
    + 3 - Requires knowledge from plugins with weight 2.

  The default weight of 3 is assigned to plugins, so each
  plugin needs to overwrite that value if needed.

  The plugins are grouped by the operating system they work
  on and then on their weight. That means that if the tool
  is run against a Windows system all plugins that support
  Windows are grouped together, and only plugins with weight
  one are run, then weight two followed by the rest of the
  plugins with the weight of three. There is no priority or
  guaranteed order of plugins that have the same weight, which
  makes it important to define the weight appropriately.
  """

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True   # pylint: disable=C6409

  # Defines the OS that this plugin supports.
  SUPPORTED_OS = []
  # Weight is an INT, with the value of 1-3.
  WEIGHT = 3

  # Defines the preprocess attribute to be set.
  ATTRIBUTE = ''

  def __init__(self, obj_store, collector):
    self._obj_store = obj_store
    self._collector = collector

  def Run(self):
    """Set the attribute of the object store to the value from GetValue."""
    setattr(self._obj_store, self.ATTRIBUTE, self.GetValue())
    logging.info(
        u'[PreProcess] Set attribute: %s to %s', self.ATTRIBUTE,
        getattr(self._obj_store, self.ATTRIBUTE, 'N/A'))

  @abc.abstractmethod
  def GetValue(self):
    raise NotImplementedError


class PlasoPreprocess(object):
  """Object used to store all information gained from preprocessing."""


class WinRegistryPreprocess(PreprocessPlugin):
  """A preprocessing class that extracts values from the Windows registry.

  By default registry needs information about system paths, which excludes
  them to run in priority 1, in some cases they may need to run in priority
  3, for instance if the registry key is dependent on which version of Windows
  is running, information that is collected during priority 2.
  """

  __abstract = True   # pylint: disable=C6409

  SUPPORTED_OS = ['Windows']
  WEIGHT = 2

  REG_KEY = '\\'
  REG_PATH = '{sysregistry}'
  REG_FILE = 'SOFTWARE'

  def GetValue(self):
    """Return the value gathered from a registry key for preprocessing."""
    sys_dir = self._collector.FindPath(self.REG_PATH)
    hive_fh = self._collector.OpenFile(u'%s/%s' % (sys_dir, self.REG_FILE))

    codepage = getattr(self._obj_store, 'code_page', 'cp1252')
    reg = win_registry.WinRegistry(hive_fh, codepage)
    key_path = self.ExpandKeyPath()
    key = reg.GetKey(key_path)

    if not key:
      raise errors.PreProcessFail(
          u'Registry key %s does not exist.' % self.REG_KEY)

    return self.ParseKey(key)

  def ExpandKeyPath(self):
    """Expand the key path with key words."""
    path = PathReplacer(self._obj_store, self.REG_KEY)
    return path.GetPath()

  @abc.abstractmethod
  def ParseKey(self, key):
    """Extract information from a registry key and save in storage."""


class PreprocessGetPath(PreprocessPlugin):
  """Return a simple path."""
  __abstract = True   # pylint: disable=C6409

  WEIGHT = 1
  ATTRIBUTE = 'nopath'
  PATH = 'doesnotexist'

  def GetValue(self):
    return self._collector.FindPath(self.PATH)


class PathReplacer(lexer.Lexer):
  """Replace path variables with values gathered from earlier preprocessing."""

  tokens = [
      lexer.Token('.', '{([^}]+)}', 'ReplaceString', ''),
      lexer.Token('.', '([^{])', 'ParseString', ''),
      ]

  def __init__(self, pre_obj, data=''):
    """Constructor for a path replacer."""
    super(PathReplacer, self).__init__(data)
    self._path = []
    self._pre_obj = pre_obj

  def GetPath(self):
    """Run the lexer and replace path."""
    while 1:
      _ = self.NextToken()
      if self.Empty():
        break

    return u''.join(self._path)

  def ParseString(self, match, **_):
    self._path.append(match.group(1))

  def ReplaceString(self, match, **_):
    replace = getattr(self._pre_obj, match.group(1), None)

    if replace:
      self._path.append(replace)
    else:
      raise errors.PathNotFound(
          u'Path variable: %s not discovered yet.', match.group(1))


class Collector(object):
  """A wrapper class to define an object for collecting data."""

  def __init__(self, pre_obj):
    """Construct the Collector.

    Args:
      pre_obj: The preprocessing object with all it's attributes that
      have been gathered so far.
    """
    self._pre_obj = pre_obj

  def FindPath(self, path_expression):
    """Return a path from a regular expression or a potentially wrong path.

    This method should attempt to find the correct file path given potentially
    limited information or a regular expression.

    Args:
      path_expression: A path to the the file in question. It can contain vague
      generic paths such as "{log_path}" or "{systemroot}" or a regular
      expression.

    Returns:
      The correct path as calculated from the source.
    """
    re_list = []
    for path_part in path_expression.split('/'):
      if '{' in path_part:
        re_list.append(self.GetExtendedPath(path_part))
      else:
        re_list.append(re.compile(r'%s' % path_part, re.I | re.S))

    return self.GetPath(re_list)

  @abc.abstractmethod
  def GetPath(self, path_list):
    """Return a path from an extended regular expression path.

    Args:
      path_list: A list of either regular expressions or expanded
      paths (strings).

    Returns:
      The string, presenting the correct path (None if not found).
    """

  def GetExtendedPath(self, path):
    """Return an extened path without the generic path elements.

    Remove common generic path elements, like {log_path}, {systemroot}
    and extend them to their real meaning.

    Args:
      path: The path before extending it.

    Returns:
      A string containing the extended path.
    """
    path = PathReplacer(self._pre_obj, path)
    return path.GetPath()

  @abc.abstractmethod
  def OpenFile(self, path):
    """Return a PFile object from a real existing path."""


class FileSystemCollector(Collector):
  """A wrapper around collecting files from mount points."""

  def __init__(self, pre_obj, mount_point):
    super(FileSystemCollector, self).__init__(pre_obj)
    self._mount_point = mount_point

  def GetPath(self, path_list):
    """Find the path on the OS if it exists."""
    real_path = u''

    for part in path_list:
      if isinstance(part, (str, unicode)):
        real_path = os.path.join(real_path, part)
      else:
        found_path = False
        for entry in os.listdir(os.path.join(self._mount_point, real_path)):
          m = part.match(entry)
          if m:
            real_path = os.path.join(real_path, m.group(0))
            found_path = True
            break
        if not found_path:
          raise errors.PathNotFound(
              u'Path not found inside %s/%s', self._mount_point, real_path)

    if not os.path.isdir(os.path.join(self._mount_point, real_path)):
      logging.warning(
          u'File path does not seem to exist (%s/%s)', self._mount_point,
          real_path)
      return None

    return real_path

  def OpenFile(self, path):
    return putils.OpenOSFile(os.path.join(self._mount_point, path))


class TSKFileCollector(Collector):
  """A wrapper around collecting files from TSK images."""

  def __init__(self, pre_obj, image_path, offset=0):
    super(TSKFileCollector, self).__init__(pre_obj)
    self._image_path = image_path
    self._image_offset = offset
    self._fs_obj = pfile.FilesystemCache.Open(image_path, offset)

  def GetPath(self, path_list):
    """Return a path."""
    real_path = u''

    for part in path_list:
      if isinstance(part, (str, unicode)):
        real_path = u'/'.join([real_path, part])
      else:
        found_path = False
        directory = self._fs_obj.fs.open_dir(real_path)
        for f in directory:
          try:
            name = f.info.name.name
            if not f.info.meta:
              continue
          except AttributeError as e:
            logging.error('[ParseImage] Problem reading file [%s], error: %s',
                          name, e)
            continue

          m = part.match(name)
          if m:
            real_path = u'/'.join([real_path, m.group(0)])
            found_path = True
            break
        if not found_path:
          raise errors.PathNotFound(
              u'Path not found inside %s', real_path)

    return real_path

  def OpenFile(self, path):
    return putils.OpenTskFile(
        path, self._image_path, int(self._image_offset / 512))


class VSSFileCollector(TSKFileCollector):
  """A wrapper around collecting files from a VSS store from an image file."""

  def __init__(self, pre_obj, image_path, store_nr, offset=0):
    super(VSSFileCollector, self).__init__(pre_obj, image_path, offset)
    self._store_nr = store_nr
    self._fs_obj = pfile.FilesystemCache.Open(
        image_path, offset, store_nr)

  def OpenFile(self, path):
    return putils.OpenVssFile(path, self._image_path, self._store_nr,
                              int(self._image_offset / 512))


