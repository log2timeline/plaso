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
"""This file contains an import statement for each plugin."""

from plaso.lib import preprocess

from plaso.preprocessors import linux
from plaso.preprocessors import win


class PreProcessList(object):
  """An object that displays all the available preprocessors."""

  def __init__(self, pre_obj, col_obj):
    """Constructor for the PreProcessList object.

    Args:
      pre_obj: A PlasoPreprocess object that contains the information
      gathered from preprocessing modules so far (and the object that
      stores future collections).
      col_obj: A collector object that defines collection methods for
      different types of sources (OS, TKS, etc.)
    """
    self._list = preprocess.PreprocessPlugin.classes
    self._pre = pre_obj
    self._col = col_obj

  def GetWeight(self, os, weight):
    """Return all preprocessors of certain weight for a particular OS."""
    ret_list = []
    for cls_obj in self._list.values():
      if os in cls_obj.SUPPORTED_OS and cls_obj.WEIGHT == weight:
        ret_list.append(cls_obj(self._pre, self._col))

    return ret_list

  def GetWeightList(self, os):
    """Return a list of all weights that are used by preprocessing plugins."""
    values = {}
    for cls_obj in self._list.values():
      if os in cls_obj.SUPPORTED_OS:
        values[cls_obj.WEIGHT] = 1

    return sorted(values.keys())

  def GetOs(self, os):
    """Return a list of all preprocessing plugins for a particular OS."""
    ret_list = []
    for cls_obj in self._list.values():
      if os in cls_obj.SUPPORTED_OS:
        ret_list.append(cls_obj(self._pre, self._col))

    return ret_list

