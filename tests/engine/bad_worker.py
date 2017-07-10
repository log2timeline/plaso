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
    option = random.randint(1, 50)
    if option == 1:
      logging.debug('Starting to bloat memory for {0:s}'.format(
          file_entry.path_spec.comparable))
      bloat = 'a'
      self._ExhaustMemory(bloat)
      logging.debug('Finished bloating memory to {0:d}'.format(len(bloat)))
    if option == 2:
      logging.debug('Never returning for {0:s}'.format(
          file_entry.path_spec.comparable))
      self._NeverReturn()
    if option == 3:
      logging.debug('Waiting 10 minutes for {0:s}'.format(
          file_entry.path_spec.comparable))
      self._TakeALongTime()
    if option == 4:
      logging.debug('Dieing on {0:s}'.format(
          file_entry.path_spec.comparable))
      self._JustDie()
    super(BadWorker, self)._ProcessFileEntryDataStream(
        mediator, file_entry, data_stream_name)

  def _ExhaustMemory(self, bloat):
    """Perpetually expand memory.

    Args:
      bloat (str): buffer to bloat
    """
    while bloat < engine.MultiProcessEngine._DEFAULT_WORKER_MEMORY_LIMIT:
      bloat += bloat
      time.sleep(2)

  def _NeverReturn(self):
    """Block forever."""
    while True:
      time.sleep(30)

  def _TakeALongTime(self):
    """Wait for 10 minutes before returning, to simulate slow processing."""
    time.sleep(10*60)

  def _JustDie(self):
    """Exits immediately."""
    sys.exit(1)