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
"""This file contains the unit tests for the queue mechanism."""
import unittest

from plaso.lib import queue


def CheckOut(q):
  return len(list(q.PopItems()))


class PlasoQueueTest(unittest.TestCase):
  """The unit test for plaso queue mechanism."""

  def testSingleQueue(self):
    my_queue = queue.SimpleQueue()
    my_queue.Queue('some stuff')
    my_queue.Queue('some stuff')
    my_queue.Queue('some stuff')
    my_queue.Queue('some stuff')

    try:
      self.assertEquals(len(my_queue), 4)
    except NotImplementedError:
      # On Mac OS X because of broken sem_getvalue()
      return
    my_queue.Close()
    self.assertEquals(CheckOut(my_queue), 4)

  def testSingleThreadedQueue(self):
    my_queue = queue.SingleThreadedQueue()
    my_queue.Queue('some stuff')
    my_queue.Queue('some stuff')
    my_queue.Queue('some stuff')
    my_queue.Queue('some stuff')

    self.assertEquals(len(my_queue), 4)
    my_queue.Close()
    self.assertEquals(CheckOut(my_queue), 4)


if __name__ == '__main__':
  unittest.main()
