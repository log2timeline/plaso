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
"""File for PyVFS migration to contain stat related functionality."""


class Stats(object):
  """Provide an object for stat results."""

  attributes = None

  def __init__(self):
    """Constructor for the stats object."""
    self.attributes = {}

  def __setattr__(self, attr, value):
    """Sets the value to either the default or the attribute store."""
    if value is None:
      return
    try:
      object.__getattribute__(self, attr)
      object.__setattr__(self, attr, value)
    except AttributeError:
      self.attributes.__setitem__(attr, value)

  def __iter__(self):
    """Return a generator that returns key/value pairs for each attribute."""
    for key, value in sorted(self.attributes.items()):
      yield key, value

  def __getattr__(self, attr):
    """Determine if attribute is set within the event or in a container."""
    try:
      return object.__getattribute__(self, attr)
    except AttributeError:
      pass

    # Check the attribute store.
    try:
      if attr in self.attributes:
        return self.attributes.__getitem__(attr)
    except TypeError as e:
      raise AttributeError('%s', e)

    raise AttributeError('Attribute not defined')
