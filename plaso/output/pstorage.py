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
"""Implements a PlasoStorage output formatter."""
import time

from plaso.lib import output
from plaso.lib import preprocess
from plaso.lib import storage


class Pstorage(output.LogOutputFormatter):
  """Dumps event objects to a plaso storage file."""

  def Start(self):
    """Sets up the output storage file."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.collection_information = {}
    pre_obj.collection_information['time_of_run'] = time.time()
    if hasattr(self._config, 'filter') and self._config.filter:
      pre_obj.collection_information['filter'] = self._config.filter
    if hasattr(self._config, 'storagefile') and self._config.storagefile:
      pre_obj.collection_information[
          'file_processed'] = self._config.storagefile
    self._storage = storage.PlasoStorage(self.filehandle, pre_obj=pre_obj)

  def EventBody(self, event_object):
    """Add an EventObject protobuf to the storage file.

    Args:
      proto: The EventObject protobuf.
    """
    self._storage.AddEntry(event_object.ToProtoString())

  def End(self):
    """Closes the storage file."""
    self._storage.CloseStorage()
