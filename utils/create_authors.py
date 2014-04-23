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
"""This file simply creates the AUTHOR file based on parser content."""

import os
import fnmatch


def ProcessFile(file_path):
  """Process a single file to match for an author tag."""
  # TODO: Change to do a "proper" import of modules and
  # check the __author__ attribute of it.
  # Current approach does not work if the author tag is a list
  # instead of a single attribute (current files as of writing do
  # not have that behavior, but that might change in the future).
  ret = ''
  with open(file_path, 'rb') as fh:
    for line in fh:
      if '__author__' in line:
        _, _, ret = line[:-1].partition(' = ')
        return ret[1:-1]


if __name__ == '__main__':
  header = """# Names should be added to this file with this pattern:
#
# For individuals:
#   Name (email address)
#
# For organizations:
#   Organization (fnmatch pattern)
#
# See python fnmatch module documentation for more information.

Google Inc. (*@google.com)
Kristinn Gudjonsson (kiddi@kiddaland.net)
Joachim Metz (joachim.metz@gmail.com)
Eric Mak (ericmak@gmail.com)
Elizabeth Schweinsberg (beth@bethlogic.net)
Keith Wall (kwallster@gmail.com)
"""
  authors = []

  with open('AUTHORS', 'wb') as out_file:
    out_file.write(header)

    for path, folders, files in os.walk('.'):
      if path in ('utils', 'tools', 'build'):
        continue
      for filematch in fnmatch.filter(files, '*.py'):
        author = ProcessFile(os.path.join(path, filematch))
        if not author:
          continue
        if type(author) in (list, tuple):
          for author_name in author:
            if author_name not in authors:
              authors.append(author)
        else:
          if author not in authors:
            authors.append(author)


    out_file.write('\n'.join(authors))
    out_file.write('\n')

  print 'Added {0:d} authors from files.'.format(len(authors))
