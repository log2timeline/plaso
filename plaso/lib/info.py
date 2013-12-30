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
"""This file provides functions for printing out information."""
import sys
import plaso
from plaso.lib import utils
from plaso.lib import putils
# TODO: Write a GetLibraryVersions that gathers all the backend parsing
# libraries and their version numbers.


def GetPluginInformation():
  """Return a string with a list of all plugin and parser information."""
  plugin_list = GetPluginData()
  return_string_pieces = []

  return_string_pieces.append(
      '{:=^80}'.format(' log2timeline/plaso information. '))

  for header, data in plugin_list.items():
    return_string_pieces.append(utils.FormatHeader(header))
    for entry_header, entry_data in data:
      return_string_pieces.append(
          utils.FormatOutputString(entry_header, entry_data))

  return u'\n'.join(return_string_pieces)


def GetPluginData():
  """Return a dict object with a list of all available parsers and plugins."""
  return_dict = {}

  # Import all plugins and parsers to print out the necessary information.
  # This is not import at top since this is only required if this parameter
  # is set, otherwise these libraries get imported in their respected
  # locations.
  # The reason why some of these libraries are imported as '_' is to make sure
  # all appropriate parsers and plugins are registered, yet we don't need to
  # directly call these libraries, it is enough to load them up to get them
  # registered.
  from plaso import filters
  from plaso import parsers as _
  from plaso import output as _
  from plaso.frontend import presets
  from plaso.lib import output
  from plaso.lib import plugin

  return_dict['Versions'] = [
      ('plaso engine', plaso.GetVersion()),
      ('python', sys.version)]

  return_dict['Parsers'] = []
  for parser in sorted(putils.FindAllParsers()['all']):
    doc_string, _, _ = parser.__doc__.partition('\n')
    return_dict['Parsers'].append((parser.parser_name, doc_string))

  return_dict['Parser Lists'] = []
  for category, parsers in sorted(presets.categories.items()):
    return_dict['Parser Lists'].append((category, ', '.join(parsers)))

  return_dict['Output Modules'] = []
  for name, description in sorted(output.ListOutputFormatters()):
    return_dict['Output Modules'].append((name, description))

  return_dict['Plugins'] = []

  for plugin, obj in sorted(plugin.BasePlugin.classes.iteritems()):
    doc_string, _, _ = obj.__doc__.partition('\n')
    return_dict['Plugins'].append((plugin, doc_string))

  return_dict['Filters'] = []
  for filter_obj in sorted(filters.ListFilters()):
    doc_string, _, _ = filter_obj.__doc__.partition('\n')
    return_dict['Filters'].append((filter_obj.filter_name, doc_string))

  return return_dict
