# -*- coding: utf-8 -*-
"""An event extraction worker that simulates various failures."""

import time
import sys
import random
import logging
from plaso.engine import worker
from plaso.multi_processing import engine

class BadWorker(worker.EventExtractionWorker):
  
  def _ProcessFileEntryDataStream(
      self, mediator, file_entry, data_stream_name):
    option = random.randint(1, 20)
    #  if option == 1:
      # self._ExhaustMemory()
    if option == 2:
      self._NeverReturn()
    if option == 3:
      self._TakeALongTime()
    if option == 4:
       self._JustDie()
    super(BadWorker, self)._ProcessFileEntryDataStream(
        mediator, file_entry, data_stream_name)

  def _ExhaustMemory(self):
    """Perpetually expand memory."""
    logging.debug('Starting to bloat memory')
    bloat = 'a'
    while bloat < engine.MultiProcessEngine._DEFAULT_WORKER_MEMORY_LIMIT:
      bloat += bloat
      time.sleep(2)

  def _NeverReturn(self):
    """Block forever."""
    logging.debug('Never returning')
    while True:
      time.sleep(30)

  def _TakeALongTime(self):
    """Wait for 10 minutes before returning, to simulate slow processing."""
    logging.debug('Waiting 10 minutes')
    time.sleep(10*60)

  def _JustDie(self):
    """Exits immediately."""
    logging.debug('Dieing')
    sys.exit(1)