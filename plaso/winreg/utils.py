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
"""This file contains Windows Registry utility functions."""

from plaso.winreg import interface


def WinRegBasename(path):
  """Determines the basename for a Windows Registry path.

  Trailing key separators are igored.

  Args:
    path: a Windows registy path with \\ as the key separator.

  Returns:
     The basename (or last path segment).
  """
  # Strip trailing key separators.
  while path and path[-1] == interface.WinRegKey.PATH_SEPARATOR:
    path = path[:-1]
  if path:
    _, _, path = path.rpartition(interface.WinRegKey.PATH_SEPARATOR)
  return path

# TOOD: create a function to return the values as a dict.
# this function should replace the repeated code blocks in multiple plugins.

# TODO: create a function to extract string data from a registry value.
