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
"""The Windows Registry key path expander."""


class WinRegistryKeyPathExpander(object):
  """Class that implements the Windows Registry key path expander object."""

  def __init__(self, pre_obj=None, reg_cache=None):
    """Initialize the path expander object.

    Args:
      pre_obj: Optional preprocess object that contains stored values from
               the image.
      reg_cache: Optional Registry objects cache (insance of WinRegistryCache).
    """
    super(WinRegistryKeyPathExpander, self).__init__()
    self._pre_obj = pre_obj
    self._reg_cache = reg_cache

  def ExpandPath(self, key_path):
    """Expand a Registry key path based on attributes in pre calculated values.

       A Registry key path may contain paths that are attributes, based on
       calculations from either preprocessing or based on each individual
       Windows Registry file.

       An attribute is defined as anything within a curly bracket, eg.
       "\\System\\{my_attribute}\\Path\\Keyname". If the attribute my_attribute
       is defined in either the pre processing object or the Registry objects
       cache it's value will be replaced with the attribute name, e.g.
       "\\System\\MyValue\\Path\\Keyname".

       If the Registry path needs to have curly brackets in the path then
       they need to be escaped with another curly bracket, eg
       "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
       case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

    Args:
      key_path: The Registry key path before being expanded.

    Returns:
      A Registry key path that's expanded based on attribute values.

    Raises:
      KeyError: If an attribute name is in the key path yet not set in
                either the Registry objects cache nor in the pre processing
                object a KeyError will be raised.
    """
    expanded_key_path = u''
    key_dict = {}
    if self._reg_cache:
      key_dict.update(self._reg_cache.attributes.items())

    if self._pre_obj:
      key_dict.update(self._pre_obj.__dict__.items())

    try:
      expanded_key_path = key_path.format(**key_dict)
    except KeyError as e:
      raise KeyError(u'Unable to expand path: {0:s}'.format(e))

    if not expanded_key_path:
      raise KeyError(u'Unable to expand path, no value returned.')

    return expanded_key_path
