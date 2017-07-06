# -*- coding: utf-8 -*-
"""An event extraction worker that simulates various failures."""

import time
import random
from plaso.engine import worker

class BadWorker(worker.EventExtractionWorker):
  
  def _ProcessFileEntryDataStream(
      self, mediator, file_entry, data_stream_name):
    option = random.randint(1, 4)
    if option == 1:
      self._ExhaustMemory()
    if option == 2:
      self._NeverReturn()
    if option == 3:
      self._TakeALongTime()
    super(BadWorker, self)._ProcessFileEntryDataStream(
        mediator, file_entry, data_stream_name)

  def _ExhaustMemory(self):
    """Perpetually expand memory."""
    bloat = 'a'
    while True:
      bloat += bloat
      time.sleep(2)

  def _NeverReturn(self):
    """Block forever."""
    while True:
      time.sleep(30)

  def _TakeALongTime(self):
    """Wait for 10 minutes before returning, to simulate slow processing."""
    time.sleep(10*60)