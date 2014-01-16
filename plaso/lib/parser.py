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
"""This file contains a class to provide a parsing framework to plaso.

This class contains a base framework class for parsing fileobjects, and
also some implementations that extend it to provide a more comprehensive
parser.
"""

import abc

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import registry


class BaseParser(object):
  """A parent class defining a typical log parser.

  This parent class gets inherited from other classes that are parsing
  log files.

  """
  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  NAME = 'base_parser'

  def __init__(self, pre_obj, config=None):
    """Parser constructor.

    Args:
      pre_obj: A preprocess object that may contain information gathered
               from a preprocessing process (instance of PreprocessObject).
      config: A configuration object, could be an instance of argparse but
              mostly an object that supports getattr to get configuration
              attributes, see a list of attributes here:
              http://plaso.kiddaland.net/developer/libraries/engine
    """
    self._pre_obj = pre_obj
    self._config = config

  @property
  def parser_name(self):
    """Return the name of the parser."""
    return self.NAME

  @abc.abstractmethod
  def Parse(self, file_entry):
    """Verifies and parses the log file and returns EventObjects.

    This is the main function of the class, the one that actually
    goes through the log file and parses each line of it to
    produce a parsed line and a timestamp.

    It also tries to verify the file structure and see if the class is capable
    of parsing the file passed to the module. It will do so with series of tests
    that should determine if the file is of the correct structure.

    If the class is not capable of parsing the file passed to it an exception
    should be raised, an exception of the type UnableToParseFile that indicates
    the reason why the class does not parse it.

    Args:
      file_entry: A file entry object.

    Raises:
      NotImplementedError when not implemented.
    """
    raise NotImplementedError


class BundleParser(BaseParser):
  """A base class for parsers that need more than a single file to parse."""

  __abstract = True

  # A list of all file patterns to match against. This list will be used by the
  # collector to find all available files to parse.
  PATTERNS = []

  @abc.abstractmethod
  def ParseBundle(self, file_entries):
    """Return a generator of EventObjects from a list of files.

    Args:
      file_entries: A list of file entry objects.

    Yields:
      EventObject for each extracted event.
    """
    pass

  def Parse(self, path_spec_bundle):
    """Return a generator for EventObjects extracted from a path bundle."""
    if not isinstance(path_spec_bundle, event.EventPathBundle):
      raise errors.UnableToParseFile(u'Not a file bundle.')

    bundle_pattern = getattr(path_spec_bundle, 'pattern', None)

    if not bundle_pattern:
      raise errors.UnableToParseFile(u'No bundle pattern defined.')

    if u'|'.join(self.PATTERNS) != bundle_pattern:
      raise errors.UnableToParseFile(u'No bundle pattern defined.')

    file_entries = list(path_spec_bundle)

    return self.ParseBundle(file_entries)
