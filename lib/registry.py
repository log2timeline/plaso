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
"""This file contains a class registration system for plugins."""

import abc


class MetaclassRegistry(abc.ABCMeta):
  """Automatic Plugin Registration through metaclasses."""

  def __init__(mcs, name, bases, env_dict):
    abc.ABCMeta.__init__(mcs, name, bases, env_dict)

    # Attach the classes dict to the baseclass and have all derived classes
    # use the same one:
    for base in bases:
      try:
        mcs.classes = base.classes
        mcs.plugin_feature = base.plugin_feature
        mcs.top_level_class = base.top_level_class
        break
      except AttributeError:
        mcs.classes = {}
        mcs.plugin_feature = mcs.__name__
        # Keep a reference to the top level class
        mcs.top_level_class = mcs

    # The following should not be registered as they are abstract. Classes
    # are abstract if the have the __abstract attribute (note this is not
    # inheritable so each abstract class must be explicitely marked).
    abstract_attribute = '_%s__abstract' % name
    if getattr(mcs, abstract_attribute, None):
      return

    if not mcs.__name__.startswith('Abstract'):
      mcs.classes[mcs.__name__] = mcs

      try:
        if mcs.top_level_class.include_plugins_as_attributes:
          setattr(mcs.top_level_class, mcs.__name__, mcs)
      except AttributeError:
        pass
