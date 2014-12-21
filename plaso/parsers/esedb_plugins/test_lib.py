#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""ESEDB plugin related functions and classes for testing."""

import pyesedb

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import single_process
from plaso.parsers import esedb
from plaso.parsers import test_lib


class EseDbPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for ESE database based plugins."""

  def _OpenEseDbFile(self, path):
    """Opens an ESE database file and returns back a pyesedb.file object.

    Args:
      path: The path to the ESE database test file.
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    file_object = file_entry.GetFileObject()
    esedb_file = pyesedb.file()

    esedb_file.open_file_object(file_object)

    return esedb_file

  def _ParseEseDbFileWithPlugin(
      self, path, plugin_object, knowledge_base_values=None):
    """Parses a file as an ESE database file and returns an event generator.

    Args:
      path: The path to the ESE database test file.
      plugin_object: The plugin object that is used to extract an event
                     generator.
      knowledge_base_values: optional dict containing the knowledge base
                             values. The default is None.

    Returns:
      An event object queue consumer object (instance of
      TestEventObjectQueueConsumer).
    """
    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = test_lib.TestEventObjectQueueConsumer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()

    parser_context = self._GetParserContext(
        event_queue, parse_error_queue,
        knowledge_base_values=knowledge_base_values)
    esedb_file = self._OpenEseDbFile(path)
    cache = esedb.EseDbCache()
    plugin_object.Process(parser_context, database=esedb_file, cache=cache)

    return event_queue_consumer
