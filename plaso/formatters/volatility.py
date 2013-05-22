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
"""This file contains a formatter for Volatility events."""
from plaso.lib import eventdata


class VolatilityFormatter(eventdata.EventFormatter):
  """Define the formatting for information extracted from Volatility."""
  DATA_TYPE = 'memory:volatility:timeliner'

  FORMAT_STRING = u'{text}'

  SOURCE_LONG = 'Application Usage'
  SOURCE_SHORT = 'RAM'

  def GetSources(self, event_object):
    """Return a list of source short and long for the event object."""
    self.source_string = getattr(event_object, 'source_type', '-')

    return super(VolatilityFormatter, self).GetSources(event_object)
