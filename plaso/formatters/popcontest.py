#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Formatter for the Popularity Contest parser events."""

from plaso.lib import eventdata


class PopularityContestSessionFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for Popularity Contest Session information."""

  DATA_TYPE = 'popularity_contest:session:event'

  FORMAT_STRING_PIECES = [
      u'Session {session}',
      u'{status}',
      u'ID {hostid}',
      u'[{details}]']

  FORMAT_STRING_SHORT_PIECES = [
      u'Session {session}',
      u'{status}']

  SOURCE_LONG = 'Popularity Contest Session'
  SOURCE_SHORT = 'LOG'


class PopularityContestLogFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for Popularity Contest Log events."""

  DATA_TYPE = 'popularity_contest:log:event'

  FORMAT_STRING_PIECES = [
      u'mru [{mru}]',
      u'package [{package}]',
      u'tag [{tag}]']

  FORMAT_STRING_SHORT_PIECES = [u'{mru}']

  SOURCE_LONG = 'Popularity Contest Log'
  SOURCE_SHORT = 'LOG'
