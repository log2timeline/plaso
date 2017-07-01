# -*- coding: utf-8 -*-
"""A multiprocessing-backed queue."""

import logging
import multiprocessing

# The 'Queue' module was renamed to 'queue' in Python 3
try:
  import Queue
except ImportError:
  import queue as Queue  # pylint: disable=import-error

from plaso.engine import plaso_queue
from plaso.lib import errors


class MultiProcessingQueue(plaso_queue.Queue):
  """Multi-processing queue."""

  def __init__(self, maximum_number_of_queued_items=0, timeout=None):
    """Initializes a multi-processing queue.

    Args:
      maximum_number_of_queued_items (Optional[int]): maximum number of queued
          items, where 0 represents no limit.
      timeout (Optional[float]): number of seconds for the get to time out,
          where None will block until a new item is put onto the queue.
    """
    super(MultiProcessingQueue, self).__init__()
    self._timeout = timeout

    # maxsize contains the maximum number of items allowed to be queued,
    # where 0 represents unlimited.

    # We need to check that we aren't asking for a bigger queue than the
    # platform supports, which requires access to this protected member.
    # pylint: disable=protected-access
    queue_max_length = multiprocessing._multiprocessing.SemLock.SEM_VALUE_MAX
    # pylint: enable=protected-access

    if maximum_number_of_queued_items > queue_max_length:
      logging.warning((
          u'Requested maximum queue size: {0:d} is larger than the maximum '
          u'size supported by the system. Defaulting to: {1:d}').format(
              maximum_number_of_queued_items, queue_max_length))
      maximum_number_of_queued_items = queue_max_length

    # This queue appears not to be FIFO.
    self._queue = multiprocessing.Queue(maxsize=maximum_number_of_queued_items)

  def Open(self):
    """Opens the queue."""
    pass

  def Close(self, abort=False):
    """Closes the queue.

    This needs to be called from any process or thread putting items onto
    the queue.

    Args:
      abort (Optional[bool]): True if the close was issued on abort.
    """
    if abort:
      # Prevent join_thread() from blocking.
      self._queue.cancel_join_thread()

    self._queue.close()
    self._queue.join_thread()

  def Empty(self):
    """Empties the queue."""
    try:
      while True:
        self._queue.get(False)
    except Queue.Empty:
      pass

  def IsEmpty(self):
    """Determines if the queue is empty."""
    return self._queue.empty()

  def PushItem(self, item, block=True):
    """Pushes an item onto the queue.

    Args:
      item (object): item to add.
      block (Optional[bool]): True to block the process when the queue is full.

    Raises:
      QueueFull: if the item could not be pushed the queue because it's full.
    """
    try:
      self._queue.put(item, block=block)
    except Queue.Full as exception:
      raise errors.QueueFull(exception)

  def PopItem(self):
    """Pops an item off the queue.

    Raises:
      QueueClose: if the queue has already been closed.
      QueueEmpty: if no item could be retrieved from the queue within the
          specified timeout.
    """
    try:
      # If no timeout is specified the queue will block if empty otherwise
      # a Queue.Empty exception is raised.
      return self._queue.get(timeout=self._timeout)

    except KeyboardInterrupt:
      raise errors.QueueClose

    # If close() is called on the multiprocessing.Queue while it is blocking
    # on get() it will raise IOError.
    except IOError:
      raise errors.QueueClose

    except Queue.Empty:
      raise errors.QueueEmpty
