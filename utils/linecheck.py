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
"""This file contains a very simple code check that pychecker misses.

All code submitted into the project goes under code review, and all code
is checked against pychecker. However pychecker doesn't check against
all conditions that are enforced in the style guide. For instance it
does not check linewidth nor if there is a whitespace at the end of a
line.

This little script is meant to "correct" that behavior, as to be a simple
addon to the pychecker checks.
"""
import os
import sys
import logging


if __name__ == '__main__':
  if not len(sys.argv) == 2:
    logging.error('Wrong usage: %s PYTHON_FILE', sys.argv[0])
    sys.exit(1)

  filename = sys.argv[1]
  if not os.path.isfile(filename):
    logging.error('Wrong usage: %s needs to be an actual file.', filename)
    sys.exit(1)

  if filename[-3:] != '.py':
    logging.error('Wrong usage: %s needs to be a python file.', filename)
    sys.exit(1)

  error_counter = 0
  with open(filename, 'rb') as fh:
    line_counter = 1
    empty_line = 0
    for line in fh:
      if line == '\n':
        empty_line += 1

      if line.startswith('class '):
        if empty_line != 2:
          print (u'Line nr %d [class declaration]: Need two empty lines before'
                 ' class declaration.') % line_counter
          error_counter += 1

      if line.startswith('def '):
        if empty_line != 2:
          print (u'Line nr %d [function declaration]: Need two empty lines befo'
                 're top level function declaration.') % line_counter
          error_counter += 1

      if line != '\n' and not (line.startswith('#') or line.startswith('@')):
        empty_line = 0

      if len(line) > 81:
        print u'Line nr %d [%d]: %s' % (line_counter, len(line), line),
        error_counter += 1

      if len(line) > 1 and line[-2] == ' ':
        print u'Line nr %d [whitespace in end]: "%s"' % (
            line_counter, line[:-1])
        error_counter += 1
      line_counter += 1

  if error_counter:
    logging.error('Lines with errors: %d', error_counter)
    sys.exit(1)
