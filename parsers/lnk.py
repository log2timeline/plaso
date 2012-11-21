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
"""This file contains a parser for the Stat object of a PFile."""
import pylnk

from plaso.lib import event
from plaso.lib import parser
from plaso.lib import timelib


class WinLnk(parser.PlasoParser):
  """Parse Windows shortcut files, or LNK files."""

  NAME = 'Shortcut File'
  PARSER_TYPE = 'LNK'

  def Parse(self, filehandle):
    """Extract EventObjects from a LNK file."""
    lnk = pylnk.file()
    lnk.open_file_object(filehandle)

    cont = event.EventContainer()
    cont.source_short = self.PARSER_TYPE
    cont.source_long = self.NAME

    texts = []

    cli = u''
    desc = u'Empty Description'

    if lnk.description:
      desc = lnk.description
      texts.append(u'[{0}] '.format(desc))

    if lnk.local_path:
      texts.append(u'Local path: {0} '.format(lnk.local_path))

    if lnk.network_path:
      texts.append(u'Network path: {0} '.format(lnk.network_path))

    if lnk.command_line_arguments:
      cli = lnk.command_line_arguments
      texts.append(u'cmd arguments: {0} '.format(cli))

    if lnk.get_environment_variables_location():
      texts.append(u'env location: {0}'.format(
          lnk.get_environment_variables_location()))

    if lnk.relative_path:
      texts.append(u'Relative path: {0} '.format(lnk.relative_path))

    if lnk.working_directory:
      texts.append(u'Working dir: {0} '.format(lnk.working_directory))

    if lnk.get_icon_location():
      texts.append(u'Icon location: {0} '.format(lnk.get_icon_location()))

    path = lnk.local_path
    if not path:
      path = lnk.network_path

    text_long = u' '.join(texts)
    cont.description_short = u'[{0}] {1} {2}'.format(
      desc, path, cli)

    if len(cont.description_short) > 80:
      cont.description_short = cont.description_short[0:79]

    evt1 = event.EventObject()
    evt1.timestamp_desc = 'Last Access'
    evt1.timestamp = timelib.WinFiletime2Unix(
        lnk.get_file_access_time_as_integer())
    evt1.description_long = text_long

    cont.Append(evt1)

    evt2 = event.EventObject()
    evt2.timestamp_desc = 'Creation Time'
    evt2.timestamp = timelib.WinFiletime2Unix(
        lnk.get_file_creation_time_as_integer())
    evt2.description_long = text_long
    cont.Append(evt2)

    evt3 = event.EventObject()
    evt3.timestamp_desc = 'Modification Time'
    evt3.timestamp = timelib.WinFiletime2Unix(
        lnk.get_file_modification_time_as_integer())
    evt3.description_long = text_long
    cont.Append(evt3)

    return cont

