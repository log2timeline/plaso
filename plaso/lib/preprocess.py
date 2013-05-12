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
import collections
import logging
import os
import re
import sre_constants

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfile
from plaso.lib import plist_interface
from plaso.lib import putils
from plaso.lib import registry
from plaso.lib import utils
from plaso.lib import win_registry

from plaso.proto import plaso_storage_pb2

from binplist import binplist
from xml.etree import ElementTree

import pytsk3
import pytz


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
  __abstract = True

  # Defines the OS that this plugin supports.
  SUPPORTED_OS = []
  # Weight is an INT, with the value of 1-3.
  WEIGHT = 3

  # Defines the preprocess attribute to be set.
  ATTRIBUTE = ''

  def __init__(self, obj_store, collector):
    """Set up the preprocessing plugin."""
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
    """Return the value for the attribute."""
    raise NotImplementedError

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.__class__.__name__


class PlasoPreprocess(object):
  """Object used to store all information gained from preprocessing."""

  def _DictToProto(self, dict_obj):
    """Return a dict message to a protobuf from a dict object."""
    proto_dict = plaso_storage_pb2.Dict()

    for dict_key, dict_value in dict_obj.items():
      sub_proto = proto_dict.attributes.add()
      event.AttributeToProto(sub_proto, dict_key, dict_value)

    return proto_dict

  def _ProtoToDict(self, proto):
    """Return a dict object from a Dict message."""
    dict_obj = {}
    for proto_dict in proto.attributes:
      dict_key, dict_value = event.AttributeFromProto(proto_dict)
      dict_obj[dict_key] = dict_value

    return dict_obj

  def FromProto(self, proto):
    """Unserializes the PlasoPreprocess from a protobuf.

    Args:
      proto: The protobuf (plaso_storage_pb2.PreProcess).

    Raises:
      RuntimeError: when the protobuf is not of type:
                    plaso_storage_pb2.PreProcess or when an unsupported
                    attribute value type is encountered
    """
    if not isinstance(proto, plaso_storage_pb2.PreProcess):
      raise RuntimeError('Unsupported proto')

    # TODO: Clear values before setting them.
    for attribute in proto.attributes:
      key, value = event.AttributeFromProto(attribute)
      if key == 'zone':
        value = pytz.timezone(value)
      setattr(self, key, value)

    if proto.HasField('counter'):
      self.counter = collections.Counter()
      dict_obj = self._ProtoToDict(proto.counter)
      for title, value in dict_obj.items():
        self.counter[title] = value

    if proto.HasField('store_range'):
      range_list = []
      for value in proto.store_range.values:
        if value.HasField('integer'):
          range_list.append(value.integer)
      self.store_range = (range_list[0], range_list[-1])

    if proto.HasField('collection_information'):
      self.collection_information = self._ProtoToDict(
          proto.collection_information)
      zone = self.collection_information.get('configure_zone')
      if zone:
        self.collection_information['configured_zone'] = pytz.timezone(zone)

  def ToProto(self):
    """Return a PreProcess protobuf built from the object."""
    proto = plaso_storage_pb2.PreProcess()

    for attribute, value in self.__dict__.items():
      if attribute == 'collection_information':
        zone = value.get('configured_zone', '')
        if zone and hasattr(zone, 'zone'):
          value['configured_zone'] = zone.zone
        proto.collection_information.MergeFrom(self._DictToProto(value))
      elif attribute == 'counter':
        value_dict = dict(value.items())
        proto.counter.MergeFrom(self._DictToProto(value_dict))
      elif attribute == 'store_range':
        range_proto = plaso_storage_pb2.Array()
        range_start = range_proto.values.add()
        range_start.integer = int(value[0])
        range_end = range_proto.values.add()
        range_end.integer = int(value[-1])
        proto.store_range.MergeFrom(range_proto)
      else:
        if attribute == 'zone':
          value = value.zone
        if isinstance(value, (bool, int, float, long)) or value:
          proto_attribute = proto.attributes.add()
          event.AttributeToProto(
              proto_attribute, attribute, value)

    return proto

  def FromProtoString(self, proto_string):
    """Unserializes the PlasoPreprocess from a serialized protobuf."""
    proto = plaso_storage_pb2.PreProcess()
    proto.ParseFromString(proto_string)
    self.FromProto(proto)

  def ToProtoString(self):
    """Serialize a PlasoPreprocess into a string value."""
    proto = self.ToProto()

    return proto.SerializeToString()


class MacPlistPreprocess(PreprocessPlugin):
  """A preprocessing class that extract values from plist files."""
  __abstract = True

  SUPPORTED_OS = ['MacOSX']
  WEIGHT = 2

  # Path to the plist file to be parsed, can depend on paths discovered
  # in previous preprocessors.
  PLIST_PATH = ''

  # The key that's value should be returned back.
  PLIST_KEY = ''

  def GetValue(self):
    """Return the value gathered from a plist file for preprocessing."""
    try:
      file_path, _, file_name = self.PLIST_PATH.rpartition('/')
      paths = self._collector.GetFilePaths(file_path, file_name)
    except errors.PathNotFound as e:
      raise errors.PreProcessFail(u'Unable to find path: %s' % e)

    if not paths:
      raise errors.PreProcessFail(u'Unable to find path: %s' % self.PLIST_PATH)

    try:
      filehandle = self._collector.OpenFile(paths[0])
    except IOError:
      raise errors.PreProcessFail(
          u'Unable to open file {}: {}'.format(paths[0], e))

    return self.ParseFile(filehandle)

  def ParseFile(self, filehandle):
    """Parse the file and return parsed key."""
    try:
      plist_file = binplist.BinaryPlist(filehandle)
      top_level_object = plist_file.Parse()
    except binplist.FormatError as e:
      raise errors.PreProcessFail(
          u'File is not a plist:{}'.format(utils.GetUnicodeString(e)))
    except OverflowError as e:
      raise errors.PreProcessFail(
          u'Error processing:{} Error:{}'.format(filehandle.display_name, e))

    if not plist_file:
      raise errors.PreProcessFail(
          u'File is not a plist:{}'.format(utils.GetUnicodeString(
              filehandle.display_name)))

    match = plist_interface.GetKeys(
        top_level_object, frozenset([self.PLIST_KEY]))

    if not match:
      raise errors.PreProcessFail(
          u'No plist keys found, trying to locate: {}'.format(self.PLIST_KEY))

    return self.ParseKey(match)

  def ParseKey(self, key):
    """Fetch the first key as defined in the PLIST_KEY and return value."""
    value = key.get(self.PLIST_KEY, None)
    if not value:
      raise errors.PreProcessFail('Value not found.')

    return value


class MacXMLPlistPreprocess(MacPlistPreprocess):
  """A preprocessing class that extract values from a XML plist file."""
  __abstract = True

  def ParseFile(self, filehandle):
    """Parse the file and return parsed key."""
    # TODO: Move to defusedxml for safer XML parsing.
    try:
      xml = ElementTree.parse(filehandle)
    except ElementTree.ParseError:
      raise errors.PreProcessFail(u'File is not a XML file.')
    except IOError:
      raise errors.PreProcessFail(u'File is not a XML file.')

    match = self._GetKeys(xml.getroot())

    if not match:
      raise errors.PreProcessFail(
          u'Keys not found inside plist file [{}].'.format(self.PLIST_KEY))

    return self.ParseKey(match)

  def _GetKeys(self, xml_root):
    """Return a dict with the requested keys."""
    match = {}

    generator = xml_root.iter()
    for key in generator:
      if 'key' in key.tag and self.PLIST_KEY in key.text:
        value_key = generator.next()
        value = ''
        for subkey in value_key.iter():
          if 'string' in subkey.tag:
            value = subkey.text
        match[key.text] = value

    # Now we need to go over the match dict and retrieve values.
    return match


class WinRegistryPreprocess(PreprocessPlugin):
  """A preprocessing class that extracts values from the Windows registry.

  By default registry needs information about system paths, which excludes
  them to run in priority 1, in some cases they may need to run in priority
  3, for instance if the registry key is dependent on which version of Windows
  is running, information that is collected during priority 2.
  """

  __abstract = True

  SUPPORTED_OS = ['Windows']
  WEIGHT = 2

  REG_KEY = '\\'
  REG_PATH = '{sysregistry}'
  REG_FILE = 'SOFTWARE'

  def GetValue(self):
    """Return the value gathered from a registry key for preprocessing."""
    sys_dirs = list(self._collector.FindPaths(self.REG_PATH))
    if not sys_dirs:
      raise errors.PreProcessFail(
          u'Unable to find file name: {}/{}'.format(
              self.REG_PATH, self.REG_FILE))

    sys_dir = sys_dirs[0]
    file_name = self._collector.GetFilePaths(sys_dir, self.REG_FILE)
    if not file_name:
      raise errors.PreProcessFail(
          u'Unable to find file name: {}/{}'.format(
              sys_dir, self.REG_FILE))

    try:
      hive_fh = self._collector.OpenFile(file_name[0])
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open file: {} [{}]'.format(file_name[0], e))

    codepage = getattr(self._obj_store, 'code_page', 'cp1252')
    try:
      reg = win_registry.WinRegistry(hive_fh, codepage)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open the registry: {} [{}] (library version:{}'.format(
              file_name[0], e, win_registry.GetLibraryVersion()))
    key_path = self.ExpandKeyPath()

    try:
      key = reg.GetKey(key_path)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Error fetching registry key: {} Error {} (library: {}'.format(
              key_path, e, win_registry.GetLibraryVersion()))

    if not key:
      raise errors.PreProcessFail(
          u'Registry key %s does not exist.' % self.REG_KEY)

    return self.ParseKey(key)

  def ExpandKeyPath(self):
    """Expand the key path with key words."""
    path = utils.PathReplacer(self._obj_store, self.REG_KEY)
    return path.GetPath()

  @abc.abstractmethod
  def ParseKey(self, key):
    """Extract information from a registry key and save in storage."""


class PreprocessGetPath(PreprocessPlugin):
  """Return a simple path."""
  __abstract = True

  WEIGHT = 1
  ATTRIBUTE = 'nopath'
  PATH = 'doesnotexist'

  def GetValue(self):
    """Return the path as found by the collector."""
    try:
      paths = list(self._collector.FindPaths(self.PATH))
    except errors.PathNotFound as e:
      raise errors.PreProcessFail(u'Unable to find path: %s' % e)
    if paths:
      return paths[0]


class Collector(object):
  """A wrapper class to define an object for collecting data."""

  def __init__(self, pre_obj):
    """Construct the Collector.

    Args:
      pre_obj: The preprocessing object with all it's attributes that
      have been gathered so far.
    """
    self._pre_obj = pre_obj

  def FindPaths(self, path_expression):
    """Return a path from a regular expression or a potentially wrong path.

    This method should attempt to find the correct file path given potentially
    limited information or a regular expression.

    Args:
      path_expression: A path to the the file in question. It can contain vague
      generic paths such as "{log_path}" or "{systemroot}" or a regular
      expression.

    Returns:
      The correct path as calculated from the source.

    Raises:
      errors.PathNotFound: If unable to compile any regular expression.
    """
    if not path_expression:
      return self.GetPaths('/')

    re_list = []
    for path_part in path_expression.split('/'):
      if not path_part:
        continue

      if '{' in path_part:
        re_list.append(self.GetExtendedPath(path_part))
      else:
        try:
          # We compile the regular expression so it matches the entire string
          # from beginning to end.
          re_list.append(re.compile(r'^%s$' % path_part, re.I | re.S))
        except sre_constants.error as e:
          logging.warning(
              u'Unable to append the following expression: %s due to %s',
              path_part, e)
          raise errors.PathNotFound(u'Unable to compile regex for path: %s', e)

    return self.GetPaths(re_list)

  @abc.abstractmethod
  def GetPaths(self, path_list):
    """Return a list of paths from an extended regular expression path.

    Args:
      path_list: A list of either regular expressions or expanded
      paths (strings).

    Returns:
      A list of strings, presenting the correct paths (None if not found).
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
    try:
      path_replacer = utils.PathReplacer(self._pre_obj, path)
      return path_replacer.GetPath()
    except errors.PathNotFound as e:
      logging.error(u'Unable to extend path %s, reason: %s', path, e)

  @abc.abstractmethod
  def GetFilePaths(self, path, file_name):
    """Return a filepath to a file given a name pattern and a path.

    Args:
      path: The correct path to the file, perhaps gathered from GetPaths
      or FindPaths.
      file_name: The filename to the file (may be a regular expression).

    Returns:
      A list of all files found that fit the pattern.
    """

  @abc.abstractmethod
  def OpenFile(self, path):
    """Return a PFile object from a real existing path."""


class FileSystemCollector(Collector):
  """A wrapper around collecting files from mount points."""

  def __init__(self, pre_obj, mount_point):
    """Initalize the filesystem collector."""
    super(FileSystemCollector, self).__init__(pre_obj)
    self._mount_point = mount_point

  def GetPaths(self, path_list):
    """Find the path on the OS if it exists."""
    paths = []

    for part in path_list:
      if isinstance(part, (str, unicode)):
        if part == '/':
          part = os.sep

        if len(paths):
          for index, path in enumerate(paths):
            paths[index] = os.path.join(path, part)
        else:
          paths.append(part)

      else:
        found_path = False
        if not paths:
          paths.append('.')

        old_paths = list(paths)
        paths = []
        for path in old_paths:
          for entry in os.listdir(os.path.join(self._mount_point, path)):
            m = part.match(entry)
            if m:
              paths.append(os.path.join(path, m.group(0)))
              found_path = True
        if not found_path:
          raise errors.PathNotFound(
              u'Path not found inside %s/%s', self._mount_point, paths)

    for real_path in paths:
      if not os.path.isdir(os.path.join(self._mount_point, real_path)):
        logging.warning(
            u'File path does not seem to exist (%s/%s)', self._mount_point,
            real_path)
        continue

      ret = real_path
      if real_path[0] == '.':
        ret = real_path[2:]

      yield ret

  def GetFilePaths(self, path, file_name):
    """Return a list of files given a path and a pattern."""
    ret = []
    file_re = re.compile(r'^%s$' % file_name, re.I | re.S)
    if path == os.sep:
      directory = self._mount_point
      path_use = '.'
    else:
      directory = os.path.join(self._mount_point, path)
      path_use = path

    for entry in os.listdir(directory):
      m = file_re.match(entry)
      if m:
        if os.path.isfile(os.path.join(directory, m.group(0))):
          ret.append(os.path.join(path_use, m.group(0)))
    return ret

  def OpenFile(self, path):
    """Open a file given a path and return a filehandle."""
    return putils.OpenOSFile(os.path.join(self._mount_point, path))


class TSKFileCollector(Collector):
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
          except IOError:
            raise errors.PathNotFound(u'Path not found inside: %s', real_path)
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
          raise errors.PathNotFound(
              u'Path not found inside %s' % real_path)

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


def GuessOS(col_obj):
  """Return a string representing what we think the underlying OS is.

  The available return strings are:
    + Windows
    + MacOSX
    + Linux

  Args:
    col_obj: The collection object.

  Returns:
     A string indicating which OS we are dealing with.
  """
  # TODO: Add error handling for WindowsError, a builtin
  # error in Windows, but not found otherwise (so no global error exists).
  # This causes the tool to crash on Windows if preprocessor is unable to
  # guess the OS, like when accidentally run against a directory.
  try:
    if list(col_obj.FindPaths('/(Windows|WINNT)/System32')):
      return 'Windows'
  except errors.PathNotFound:
    pass

  try:
    if list(col_obj.FindPaths('/System/Library')):
      return 'MacOSX'
  except errors.PathNotFound:
    pass

  try:
    if list(col_obj.FindPaths('/etc')):
      return 'Linux'
  except errors.PathNotFound:
    pass

  return 'None'
