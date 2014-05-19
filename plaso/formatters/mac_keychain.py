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
"""Formatter for the Keychain password database file."""

from plaso.lib import eventdata


class KeychainApplicationRecordFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for keychain application record event."""

  DATA_TYPE = 'mac:keychain:application'

  FORMAT_STRING_PIECES = [
      u'Name: {entry_name}',
      u'Account: {account_name}']

  FORMAT_STRING_SHORT_PIECES = [u'{entry_name}']

  SOURCE_LONG = 'Keychain Application password'
  SOURCE_SHORT = 'LOG'


class KeychainInternetRecordFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for keychain internet record event."""

  DATA_TYPE = 'mac:keychain:internet'

  FORMAT_STRING_PIECES = [
      u'Name: {entry_name}',
      u'Account: {account_name}',
      u'Where: {where}',
      u'Protocol: {protocol}',
      u'({type_protocol})']

  FORMAT_STRING_SHORT_PIECES = [u'{entry_name}']

  SOURCE_LONG = 'Keychain Internet password'
  SOURCE_SHORT = 'LOG'
