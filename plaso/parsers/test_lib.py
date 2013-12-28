#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Parser related functions and classes for testing."""

from plaso.pvfs import pfile
from plaso.pvfs import utils


def ParseFile(parser_object, filename):
  """Parses a file using the parser class.

  Args:
    parser_object: the parser object.
    filename: the name of the file to parse.

  Returns:
    A list of event objects.
  """
  # TODO: Make the changes proposed in CL 38080044.
  file_entry = utils.OpenOSFileEntry(filename)
  return list(parser_object.Parse(file_entry))


def ParseFileByPathSpec(parser_object, path_spec, fscache=None):
  """Parses a file using the parser class.

  Args:
    parser_object: the parser object.
    path_spect: the path specification of the file to parse.
    fscache: optional file system cache object. The default is None.

  Returns:
    A list of event objects.
  """
  file_entry = pfile.OpenPFileEntry(path_spec, fscache=fscache)
  return list(parser_object.Parse(file_entry))
