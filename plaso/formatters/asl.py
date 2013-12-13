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

"""Formatter for the Apple System Log binary files."""

from plaso.lib import eventdata


class AslFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for an ASL log entry."""
  DATA_TYPE = 'mac:asl:event'

  FORMAT_STRING_PIECES = [
      u'MessageID: {message_id}',
      u'Level: {level}',
      u'User ID: {user_sid}',
      u'Group ID: {group_id}',
      u'Read User: {read_uid}',
      u'Read Group: {read_gid}',
      u'Host: {computer_name}',
      u'Sender: {sender}',
      u'Facility: {facility}',
      u'Message: {message}',
      u'{extra_information}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Host: {host}',
      u'Sender: {sender}',
      u'Facility: {facility}']

  SOURCE_LONG = 'ASL entry'
  SOURCE_SHORT = 'LOG'

