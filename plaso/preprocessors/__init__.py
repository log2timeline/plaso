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
"""This file contains an import statement for each plugin."""

from plaso.preprocessors import interface
from plaso.preprocessors import linux
from plaso.preprocessors import macosx
from plaso.preprocessors import windows


class PreProcessorsManager(object):
  """Class that implements the pre-processors manager."""

  _list = interface.PreprocessPlugin.classes

  @classmethod
  def GetWeight(cls, platform, weight):
    """Returns all preprocessors of certain weight for a particular OS.

    Args:
      platform: A string containing the operating system name.
    """
    ret_list = []
    for cls_obj in cls._list.values():
      if platform in cls_obj.SUPPORTED_OS and cls_obj.WEIGHT == weight:
        ret_list.append(cls_obj())

    return ret_list

  @classmethod
  def GetWeightList(cls, platform):
    """Returns a list of all weights that are used by preprocessing plugins.

    Args:
      platform: A string containing the operating system name.
    """
    values = {}
    for cls_obj in cls._list.values():
      if platform in cls_obj.SUPPORTED_OS:
        values[cls_obj.WEIGHT] = 1

    return sorted(values.keys())

  @classmethod
  def GetOs(cls, platform):
    """Returns a list of all preprocessing plugins for a particular OS.

    Args:
      platform: A string containing the operating system name.
    """
    ret_list = []
    for cls_obj in cls._list.values():
      if platform in cls_obj.SUPPORTED_OS:
        ret_list.append(cls_obj())

    return ret_list
