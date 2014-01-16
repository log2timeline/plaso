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
"""This file contains preprocessors for Linux."""

import csv

from plaso.lib import preprocess_interface


class LinuxHostname(preprocess_interface.PreprocessPlugin):
  """A preprocessing class that fetches hostname on Linux."""

  SUPPORTED_OS = ['Linux']
  WEIGHT = 1
  ATTRIBUTE = 'hostname'

  def GetValue(self):
    """Return the hostname."""
    file_entry = self._collector.OpenFileEntry(u'/etc/hostname')
    file_object = file_entry.Open()
    result = u'%s' % file_object.read(512)
    file_object.close()
    return result


class LinuxUsernames(preprocess_interface.PreprocessPlugin):
  """A preprocessing class that fetches usernames on Linux."""

  SUPPORTED_OS = ['Linux']
  WEIGHT = 1
  ATTRIBUTE = 'users'

  def GetValue(self):
    """Return the user information."""
    # TODO: Add passwd.cache, might be good if nss cache is enabled.
    file_entry = self._collector.OpenFileEntry('/etc/passwd')
    file_object = file_entry.Open()

    users = []
    reader = csv.reader(file_object, delimiter=':')

    for row in reader:
      user = {}
      user['uid'] = row[2]
      user['gid'] = row[3]
      user['name'] = row[0]
      user['path'] = row[5]
      user['shell'] = row[6]
      users.append(user)

    file_object.close()
    return users
