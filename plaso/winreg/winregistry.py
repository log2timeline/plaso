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
"""This file contains the Windows Registry class."""

from plaso.winreg import interface
from plaso.winreg import winpyregf


class WinRegistry(object):
  """Class to provided a uniform way to access the Windows Registry."""

  BACKEND_PYREGF = 1

  _KNOWN_KEYS = {
      'NTUSER.DAT': '\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',
      'SAM': '\\SAM\\Domains\\Account\\Users',
      'SECURITY': '\\Policy\\PolAdtEv',
      'SOFTWARE': '\\Microsoft\\Windows\\CurrentVersion\\App Paths',
      'SYSTEM': '\\Select',
  }

  # TODO: this list is not finished yet and will need some more research.
  # For now an empty string represent the root and None an unknown or
  # not mounted.
  _FILENAME_MOUNTED_PATHS = {
      'DEFAULT': None,
      'NTUSER.DAT': 'HKEY_CURRENT_USER',
      'NTUSER.MAN': None,
      'REG.DAT': '',
      'SAM': 'HKEY_LOCAL_MACHINE\\SAM',
      'SECURITY': 'HKEY_LOCAL_MACHINE\\Security',
      'SOFTWARE': 'HKEY_LOCAL_MACHINE\\Software',
      'SYSTEM': 'HKEY_LOCAL_MACHINE\\System',
      'SYSCACHE.HVE': None,
      'SYSTEM.DAT': 'HKEY_LOCAL_MACHINE',
      'USERDIFF': None,
      'USERS.DAT': 'HKEY_USERS',
      'USRCLASS.DAT': 'HKEY_CURRENT_USER\\Software\\Classes',
  }

  def __init__(self, backend=1):
    """Initializes the Windows Registry.

    Args:
      backend: The back-end to use to read the Registry structures, the
               default is 1 (pyregf).
    """
    self._backend = backend
    self._files = {}

  @classmethod
  def GetMountedPath(cls, filename):
    """Determines the mounted path based on the filename.

    Args:
      filename: The name of the Registry file.

    Returns:
      The mounted path if successful or None otherwise.
    """
    return cls._FILENAME_MOUNTED_PATHS.get(filename.upper(), None)

  def OpenFile(self, file_object, codepage='cp1252'):
    """Opens the file object based on the back-end.

    Args:
      file_object: The file-like object of the Registry file.

    Returns:
      The a Windows Registry file (an instance of WinRegFile) if successful
      or None otherwise.
    """
    winreg_file = None

    if self._backend == self.BACKEND_PYREGF:
      winreg_file = winpyregf.WinPyregfFile()

    if winreg_file:
      winreg_file.Open(file_object, codepage=codepage)

    return winreg_file

  def MountFile(self, winreg_file, mounted_path):
    """Mounts a file in the Registry.

    Args:
      winreg_file: The Windows Registry file (an instance of WinRegFile).
      mounted_path: The path of the key where the Registry file is mounted.

    Raises:
      KeyError: if mounted path is already set.
      ValueError: if mounted path is not set.
    """
    if not mounted_path:
      raise ValueError(u'Missing mounted path value')

    if mounted_path in self._files:
      raise KeyError(u'Mounted path: {0:s} already set.'.format(mounted_path))

    self._files[mounted_path] = winreg_file

  def GetKeyByPath(self, path):
    """Retrieves a specific key defined by the Registry path.

    Returns:
      The key (an instance of WinRegKey) if available or None otherwise.
    """
    for mounted_path in self._files.keys():
      if path.startswith(mounted_path):
        break

    if not mounted_path:
      return None

    winreg_file = self._files[mounted_path]

    mounted_path_length = len(mounted_path)

    if mounted_path.endswith(interface.WinRegKey.PATH_SEPARATOR):
      mounted_path_length -= 1

    path = path[mounted_path_length:]

    if not winreg_file:
      return None

    winreg_key = winreg_file.GetKeyByPath(path)

    # TODO: correct the path of the key for the mounted location.

    return winreg_key
