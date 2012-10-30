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
"""This file contains the unit tests for the storage mechanism of Plaso."""
import tempfile
import unittest
import zipfile

from plaso.lib import event
from plaso.lib import storage
from plaso.proto import plaso_storage_pb2


class PlasoStorageUnitTest(unittest.TestCase):
  """The unit test for plaso storage."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.events = []
    event_1 = event.RegistryEvent(
        u'MY AutoRun key', {u'Value': u'c:/Temp/evil.exe'}, 13349615269295969)
    event_1.source_long = 'NTUSER.DAT Registry File'
    event_2 = event.RegistryEvent(
        u'\\HKCU\\Secret\\EvilEmpire\\Malicious_key',
        {u'Value': u'send all the exes to the other world'}, 13359662069295961)
    event_2.source_long = 'NTUSER.DAT Registry File'
    event_3 = event.RegistryEvent(
        u'\\HKCU\\Windows\\Normal', {u'Value': u'run all the benign stuff'},
        13349402860000000)
    event_3.source_long = 'NTUSER.DAT Registry File'
    event_4 = event.TextEvent(12389344590000000,
                              ('This is a line by someone not reading the log'
                               ' line properly. And since this log line exceed'
                               's the accepted 80 chars it will be '
                               'shortened.'), 'Some random text file',
                              'nomachine', 'johndoe')
    self.events.append(event_1)
    self.events.append(event_2)
    self.events.append(event_3)
    self.events.append(event_4)

  def testStorageDumper(self):
    self.assertEquals(len(self.events), 4)

    with tempfile.NamedTemporaryFile() as fh:
      # The dumper is normally run in another thread, but for the purpose
      # of this test it is run in sequence, hence the call to .Run() after
      # all has been queued up.
      dumper = storage.SimpleStorageDumper(fh)
      for e in self.events:
        dumper.AddEvent(e)
      dumper.Close()
      dumper.Run()

      z_file = zipfile.ZipFile(fh, 'r', zipfile.ZIP_DEFLATED)
      self.assertEquals(len(z_file.namelist()), 3)

      self.assertEquals(sorted(z_file.namelist()), ['plaso_index.000001',
                                                    'plaso_meta.000001',
                                                    'plaso_proto.000001'])

  def testStorage(self):
    protos = []
    timestamps = []
    with tempfile.NamedTemporaryFile() as fh:
      store = storage.PlasoStorage(fh)

      for my_event in self.events:
        store.AddEntry(my_event)

      store.CloseStorage()

      read_store = storage.PlasoStorage(fh, True)

      for proto in read_store.GetEntries(1):
        protos.append(proto)
        timestamps.append(proto.timestamp)
        if proto.source_short == plaso_storage_pb2.EventObject.REG:
          self.assertEquals(proto.source_long, 'NTUSER.DAT Registry File')
          self.assertEquals(proto.timestamp_desc, 'Last Written')
        else:
          self.assertEquals(proto.source_long, 'Some random text file')
          self.assertEquals(proto.timestamp_desc, 'Entry Written')

    self.assertEquals(len(protos), 4)

    self.assertEquals(timestamps, [12389344590000000, 13349402860000000,
                                   13349615269295969, 13359662069295961])


if __name__ == '__main__':
  unittest.main()
