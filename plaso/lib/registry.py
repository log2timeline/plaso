#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a class registration system for plugins."""

import abc


class MetaclassRegistry(abc.ABCMeta):
  """Automatic Plugin Registration through metaclasses."""

  def __init__(cls, name, bases, env_dict):
    abc.ABCMeta.__init__(cls, name, bases, env_dict)

    # Register the name of the immedient parent class.
    if bases:
      cls.parent_class = getattr(bases[0], 'NAME', bases[0])

    # Attach the classes dict to the baseclass and have all derived classes
    # use the same one:
    for base in bases:
      try:
        cls.classes = base.classes
        cls.plugin_feature = base.plugin_feature
        cls.top_level_class = base.top_level_class
        break
      except AttributeError:
        cls.classes = {}
        cls.plugin_feature = cls.__name__
        # Keep a reference to the top level class
        cls.top_level_class = cls

    # The following should not be registered as they are abstract. Classes
    # are abstract if the have the __abstract attribute (note this is not
    # inheritable so each abstract class must be explicitely marked).
    abstract_attribute = '_%s__abstract' % name
    if getattr(cls, abstract_attribute, None):
      return

    if not cls.__name__.startswith('Abstract'):
      if hasattr(cls, 'NAME'):
        cls.classes[cls.NAME] = cls
      else:
        cls.classes[cls.__name__] = cls

      try:
        if cls.top_level_class.include_plugins_as_attributes:
          setattr(cls.top_level_class, cls.__name__, cls)
      except AttributeError:
        pass
