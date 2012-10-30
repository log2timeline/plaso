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
"""This file contains a test for UserAssist parsing in Plaso."""
import os
import unittest

from plaso.lib import win_registry
from plaso.registry import xpuserassist


class RegistryXPUserAssistTest(unittest.TestCase):
  """The unit test for XP UserAssist parsing."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = os.path.join('plaso/test_data')
    self.registry_file = os.path.join(self.base_path, 'NTUSER.DAT')
    fh = open(self.registry_file, 'rb')
    self.registry = win_registry.WinRegistry(fh)

  def testUserAssist(self):
    key = self.registry.GetKey(('\\Software\\Microsoft\\Windows\\CurrentVersio'
                                'n\\Explorer\\UserAssist\\{75048700-EF1F-11D0-'
                                '9888-006097DEACF9}\\Count'))
    plugin = xpuserassist.XPUserAssistPlugin(None)
    entries = list(plugin.Process(key))

    self.assertEquals(entries[0].timestamp, 1249398682811068)
    self.assertEquals(entries[0].description_long,
                      u'UEME_RUNPIDL:%csidl2%\\MSN.lnk: [Count: 14]')


if __name__ == '__main__':
  unittest.main()
