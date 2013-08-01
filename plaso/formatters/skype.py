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
"""Formatter for the Skype Main database events."""
from plaso.lib import eventdata


class SkypeAccountFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for Skype Account information."""
  DATA_TYPE = 'skype:event:account'

  FORMAT_STRING_PIECES = [u'{username}', u'[{email}]', u'Country: {country}']

  SOURCE_LONG = 'Skype Account'
  SOURCE_SHORT = 'LOG'


class SkypeChatFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for Skype chat events."""
  DATA_TYPE = 'skype:event:chat'

  FORMAT_STRING_PIECES = [
      u'From: {from_account}',
      u'To: {to_account}',
      u'Message: {text}',
      u'[{title}]']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = 'Skype Chat MSG'
  SOURCE_SHORT = 'LOG'
