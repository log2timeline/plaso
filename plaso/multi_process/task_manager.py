# -*- coding: utf-8 -*-
"""The task manager."""

import collections
import heapq
import threading
import time

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.containers import tasks
from plaso.lib import definitions
from plaso.engine import processing_status
from plaso.engine import profilers
from plaso.multi_process import logger


class _PendingMergeTaskHeap(object):
  """Heap to manage pending merge tasks."""

  def __init__(self):
    """Initializes a pending merge task heap."""
    super(_PendingMergeTaskHeap, self).__init__()
    self._heap = []
    self._task_identifiers = set()

  def __contains__(self, task_identifier):
    """Checks for an task identifier being present in the heap.

    Args:
      task_identifier (str): task identifier to check for.

    Returns:
      bool: True if the task with the given identifier is present in the heap.
    """
    return task_identifier in self._task_identifiers

  def __len__(self):
    """Determines the number of tasks on the heap.

    Returns:
      int: number of tasks on the heap.
    """
    return len(self._heap)

  def PeekTask(self):
    """Retrieves the first task from the heap without removing it.

    Returns:
      Task: task or None if the heap is empty.
    """
    try:
      _, task = self._heap[0]

    except IndexError:
      return None

    return task

  def PopTask(self):
    """Retrieves and removes the first task from the heap.

    Returns:
      Task: the task or None if the heap is empty.
    """
    try:
      _, task = heapq.heappop(self._heap)

    except IndexError:
      return None
    self._task_identifiers.remove(task.identifier)
    return task

  def PushTask(self, task):
    """Pushes a task onto the heap.

    Args:
      task (Task): task.

    Raises:
      ValueError: if the size of the storage file is not set in the task.
    """
    storage_file_size = getattr(task, 'storage_file_size', None)
    if not storage_file_size:
      raise ValueError('Task storage file size not set.')

    # Prioritize directories over files and other types of file entries to try
    # to prevent merge depletion.
    if task.file_entry_type == dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY:
      weight = -1
    else:
      weight = storage_file_size

    task.merge_priority = weight

    heap_values = (weight, task)
    heapq.heappush(self._heap, heap_values)
    self._task_identifiers.add(task.identifier)


class TaskManager(object):
  """Manages tasks and tracks their completion and status.

  A task being tracked by the manager must be in exactly one of the
  following states:

  * abandoned: a task assumed to be abandoned because a tasks that has been
      queued or was processing exceeds the maximum inactive time.
  * merging: a task that is being merged by the engine.
  * pending_merge: the task has been processed and is ready to be merged with
      the session storage.
  * processed: a worker has completed processing the task, but it is not ready
      to be merged into the session storage.
  * processing: a worker is processing the task.
  * queued: the task is waiting for a worker to start processing it. It is also
      possible that a worker has already completed the task, but no status
      update was collected from the worker while it processed the task.

  Once the engine reports that a task is completely merged, it is removed
  from the task manager.

  Tasks are considered "pending" when there is more work that needs to be done
  to complete these tasks. Pending applies to tasks that are:
  * not abandoned;
  * abandoned, but need to be retried.

  Abandoned tasks without corresponding retry tasks are considered "failed"
  when the foreman is done processing.
  """

  # Stop pylint from reporting:
  # Context manager 'lock' doesn't implement __enter__ and __exit__.
  # pylint: disable=not-context-manager

  # Consider a task inactive after 5 minutes of no activity.
  _TASK_INACTIVE_TIME = 5.0 * 60.0

  def __init__(self):
    """Initializes a task manager."""
    super(TaskManager, self).__init__()
    self._lock = threading.Lock()

    # This dictionary maps task identifiers to tasks that have been abandoned,
    # as no worker has reported processing the task in the expected interval.
    self._tasks_abandoned = {}

    # The latest processing time observed in a task. This value is set to
    # the current time to not have to handle None as a special case.
    self._latest_task_processing_time = int(
        time.time() * definitions.MICROSECONDS_PER_SECOND)

    # This dictionary maps task identifiers to tasks that are being merged
    # by the foreman.
    self._tasks_merging = {}

    # Use ordered dictionary to preserve the order in which tasks were added.
    # This dictionary maps task identifiers to tasks that are waiting to be
    # processed.
    self._tasks_queued = collections.OrderedDict()

    self._tasks_pending_merge = _PendingMergeTaskHeap()

    # This dictionary maps task identifiers to tasks that are currently
    # being processed by a worker.
    self._tasks_processing = {}

    self._tasks_profiler = None

    # TODO: implement a limit on the number of tasks.
    self._total_number_of_tasks = 0

  def _AbandonInactiveProcessingTasks(self):
    """Marks processing tasks that exceed the inactive time as abandoned.

    This method does not lock the manager and should be called by a method
    holding the manager lock.
    """
    if self._tasks_processing:
      inactive_time = time.time() - self._TASK_INACTIVE_TIME
      inactive_time = int(inactive_time * definitions.MICROSECONDS_PER_SECOND)

      # Abandon all tasks after they're identified so as not to modify the
      # dict while iterating over it.
      tasks_to_abandon = []
      for task_identifier, task in self._tasks_processing.items():
        if task.last_processing_time < inactive_time:
          logger.debug('Abandoned processing task: {0:s}.'.format(
              task_identifier))

          self.SampleTaskStatus(task, 'abandoned_processing')
          tasks_to_abandon.append((task_identifier, task))

      for task_identifier, task in tasks_to_abandon:
        self._tasks_abandoned[task_identifier] = task
        del self._tasks_processing[task_identifier]

  def _AbandonQueuedTasks(self):
    """Marks queued tasks abandoned.

    This method does not lock the manager and should be called by a method
    holding the manager lock.
    """
    # Abandon all tasks after they're identified so as not to modify the
    # dict while iterating over it.
    tasks_to_abandon = []
    for task_identifier, task in self._tasks_queued.items():
      logger.debug('Abandoned queued task: {0:s}.'.format(task_identifier))
      tasks_to_abandon.append((task_identifier, task))

    for task_identifier, task in tasks_to_abandon:
      self._tasks_abandoned[task_identifier] = task
      del self._tasks_queued[task_identifier]

  def _GetTaskPendingRetry(self):
    """Retrieves an abandoned task that should be retried.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Returns:
      Task: a task that was abandoned but should be retried or None if there are
          no abandoned tasks that should be retried.
    """
    for task in self._tasks_abandoned.values():
      if not task.has_retry:
        return task

    return None

  def _HasTasksPendingMerge(self):
    """Determines if there are tasks waiting to be merged.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Returns:
      bool: True if there are abandoned tasks that need to be retried.
    """
    return bool(self._tasks_pending_merge)

  def _HasTasksPendingRetry(self):
    """Determines if there are abandoned tasks that still need to be retried.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Returns:
      bool: True if there are abandoned tasks that need to be retried.
    """
    return bool(self._GetTaskPendingRetry())

  def _UpdateLatestProcessingTime(self, task):
    """Updates the latest processing time of the task manager from the task.

    This method does not lock the manager and should be called by a method
    holding the manager lock.

    Args:
      task (Task): task to update the processing time of.
    """
    self._latest_task_processing_time = max(
        self._latest_task_processing_time, task.last_processing_time)

  def CheckTaskToMerge(self, task):
    """Checks if the task should be merged.

    Args:
      task (Task): task.

    Returns:
      bool: True if the task should be merged.

    Raises:
      KeyError: if the task was not queued, processing or abandoned.
    """
    with self._lock:
      is_abandoned = task.identifier in self._tasks_abandoned
      is_processing = task.identifier in self._tasks_processing
      is_queued = task.identifier in self._tasks_queued

      if not is_queued and not is_processing and not is_abandoned:
        raise KeyError('Status of task {0:s} is unknown.'.format(
            task.identifier))

      return is_queued or is_processing or is_abandoned and not task.has_retry

  def CreateRetryTask(self):
    """Creates a task that to retry a previously abandoned task.

    Returns:
      Task: a task that was abandoned but should be retried or None if there are
          no abandoned tasks that should be retried.
    """
    with self._lock:
      abandoned_task = self._GetTaskPendingRetry()
      if not abandoned_task:
        return None

      # The abandoned task is kept in _tasks_abandoned so it can be still
      # identified in CheckTaskToMerge and UpdateTaskAsPendingMerge.

      retry_task = abandoned_task.CreateRetryTask()
      logger.debug('Retrying task {0:s} as {1:s}.'.format(
          abandoned_task.identifier, retry_task.identifier))

      self._tasks_queued[retry_task.identifier] = retry_task
      self._total_number_of_tasks += 1

      self.SampleTaskStatus(retry_task, 'created_retry')

      return retry_task

  # TODO: add support for task types.
  def CreateTask(
      self, session_identifier,
      storage_format=definitions.STORAGE_FORMAT_SQLITE):
    """Creates a task.

    Args:
      session_identifier (str): the identifier of the session the task is
          part of.
      storage_format (Optional[str]): the storage format that the task should be
          stored in.

    Returns:
      Task: task attribute container.
    """
    task = tasks.Task(session_identifier)
    task.storage_format = storage_format
    logger.debug('Created task: {0:s}.'.format(task.identifier))

    with self._lock:
      self._tasks_queued[task.identifier] = task
      self._total_number_of_tasks += 1

      self.SampleTaskStatus(task, 'created')

    return task

  def CompleteTask(self, task):
    """Completes a task.

    The task is complete and can be removed from the task manager.

    Args:
      task (Task): task.

    Raises:
      KeyError: if the task was not merging.
    """
    with self._lock:
      if task.identifier not in self._tasks_merging:
        raise KeyError('Task {0:s} was not merging.'.format(task.identifier))

      self.SampleTaskStatus(task, 'completed')

      del self._tasks_merging[task.identifier]

      logger.debug('Completed task {0:s}.'.format(task.identifier))

  def GetFailedTasks(self):
    """Retrieves all failed tasks.

    Failed tasks are tasks that were abandoned and have no retry task once
    the foreman is done processing.

    Returns:
      list[Task]: tasks.
    """
    # TODO: add check to determine foreman is done processing.

    with self._lock:
      return [task for task in self._tasks_abandoned.values()
              if not task.has_retry]

  def GetProcessedTaskByIdentifier(self, task_identifier):
    """Retrieves a task that has been processed.

    Args:
      task_identifier (str): unique identifier of the task.

    Returns:
      Task: a task that has been processed.

    Raises:
      KeyError: if the task was not processing, queued or abandoned.
    """
    with self._lock:
      task = self._tasks_processing.get(task_identifier, None)
      if not task:
        task = self._tasks_queued.get(task_identifier, None)
      if not task:
        task = self._tasks_abandoned.get(task_identifier, None)
      if not task:
        raise KeyError('Status of task {0:s} is unknown'.format(
            task_identifier))

    return task

  def GetStatusInformation(self):
    """Retrieves status information about the tasks.

    Returns:
      TasksStatus: tasks status information.
    """
    status = processing_status.TasksStatus()

    with self._lock:
      status.number_of_abandoned_tasks = len(self._tasks_abandoned)
      status.number_of_queued_tasks = len(self._tasks_queued)
      status.number_of_tasks_pending_merge = (
          len(self._tasks_pending_merge) + len(self._tasks_merging))
      status.number_of_tasks_processing = len(self._tasks_processing)
      status.total_number_of_tasks = self._total_number_of_tasks

    return status

  def GetTaskPendingMerge(self, current_task):
    """Retrieves the first task that is pending merge or has a higher priority.

    This function will check if there is a task with a higher merge priority
    than the current_task being merged. If so, that task with the higher
    priority is returned.

    Args:
      current_task (Task): current task being merged or None if no such task.

    Returns:
      Task: the next task to merge or None if there is no task pending merge or
          with a higher priority.
    """
    next_task = self._tasks_pending_merge.PeekTask()
    if not next_task:
      return None

    if current_task and next_task.merge_priority > current_task.merge_priority:
      return None

    with self._lock:
      next_task = self._tasks_pending_merge.PopTask()

    self._tasks_merging[next_task.identifier] = next_task
    return next_task

  def HasPendingTasks(self):
    """Determines if there are tasks running or in need of retrying.

    Returns:
      bool: True if there are tasks that are active, ready to be merged or
          need to be retried.
    """
    logger.debug('Checking for pending tasks')
    with self._lock:
      self._AbandonInactiveProcessingTasks()

      if self._tasks_processing:
        return True

      # There are no tasks being processed, but we might be
      # waiting for some tasks to be merged.
      if self._HasTasksPendingMerge():
        return True

      # There are no tasks processing or pending merge, but there may
      # still be some waiting to be retried, so we check that.
      if self._HasTasksPendingRetry():
        return True

      # It is possible that a worker has processed a task and the foreman has
      # not been informed about it, since there is no feedback from the worker
      # when it pops a task from the queue.

      # If we believe all the workers are idle for longer than the task
      # inactive time (timeout) abandon all queued tasks. This ensures
      # that processing actually stops when the foreman never gets an
      # update from a worker.

      if self._tasks_queued:
        inactive_time = time.time() - self._TASK_INACTIVE_TIME
        inactive_time = int(inactive_time * definitions.MICROSECONDS_PER_SECOND)

        if self._latest_task_processing_time < inactive_time:
          self._AbandonQueuedTasks()

      if self._tasks_queued:
        return True

      if self._tasks_merging:
        return True

    # There are no tasks pending any work.
    return False

  def RemoveTask(self, task):
    """Removes an abandoned task.

    Args:
      task (Task): task.

    Raises:
      KeyError: if the task was not abandoned or the task was abandoned and
          was not retried.
    """
    with self._lock:
      if task.identifier not in self._tasks_abandoned:
        raise KeyError('Task {0:s} was not abandoned.'.format(task.identifier))

      if not task.has_retry:
        raise KeyError(
            'Will not remove a task {0:s} without retry task.'.format(
                task.identifier))

      del self._tasks_abandoned[task.identifier]

      logger.debug('Removed task {0:s}.'.format(task.identifier))

  def SampleTaskStatus(self, task, status):
    """Takes a sample of the status of the task for profiling.

    Args:
      task (Task): a task.
      status (str): status.
    """
    if self._tasks_profiler:
      self._tasks_profiler.Sample(task, status)

  def StartProfiling(self, configuration, identifier):
    """Starts profiling.

    Args:
      configuration (ProfilingConfiguration): profiling configuration.
      identifier (str): identifier of the profiling session used to create
          the sample filename.
    """
    if not configuration:
      return

    if configuration.HaveProfileTasks():
      self._tasks_profiler = profilers.TasksProfiler(identifier, configuration)
      self._tasks_profiler.Start()

  def StopProfiling(self):
    """Stops profiling."""
    if self._tasks_profiler:
      self._tasks_profiler.Stop()
      self._tasks_profiler = None

  def UpdateTaskAsPendingMerge(self, task):
    """Updates the task manager to reflect that the task is ready to be merged.

    Args:
      task (Task): task.

    Raises:
      KeyError: if the task was not queued, processing or abandoned, or
          the task was abandoned and has a retry task.
    """
    with self._lock:
      is_abandoned = task.identifier in self._tasks_abandoned
      is_processing = task.identifier in self._tasks_processing
      is_queued = task.identifier in self._tasks_queued

      if not is_queued and not is_processing and not is_abandoned:
        raise KeyError('Status of task {0:s} is unknown.'.format(
            task.identifier))

      if is_abandoned and task.has_retry:
        raise KeyError('Will not merge a task {0:s} with retry task.'.format(
            task.identifier))

      if is_queued:
        logger.debug('Task {0:s} was queued, now merging.'.format(
            task.identifier))
        del self._tasks_queued[task.identifier]

      if is_processing:
        logger.debug('Task {0:s} was processing, now merging.'.format(
            task.identifier))
        del self._tasks_processing[task.identifier]

      if is_abandoned:
        logger.debug('Task {0:s} was abandoned, now merging.'.format(
            task.identifier))
        del self._tasks_abandoned[task.identifier]

      self._tasks_pending_merge.PushTask(task)

      self.SampleTaskStatus(task, 'pending_merge')

      task.UpdateProcessingTime()
      self._UpdateLatestProcessingTime(task)

  def UpdateTaskAsProcessingByIdentifier(self, task_identifier):
    """Updates the task manager to reflect the task is processing.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not known to the task manager.
    """
    with self._lock:
      task_processing = self._tasks_processing.get(task_identifier, None)
      if task_processing:
        task_processing.UpdateProcessingTime()
        self._UpdateLatestProcessingTime(task_processing)
        return

      task_queued = self._tasks_queued.get(task_identifier, None)
      if task_queued:
        logger.debug('Task {0:s} was queued, now processing.'.format(
            task_identifier))
        self._tasks_processing[task_identifier] = task_queued
        del self._tasks_queued[task_identifier]

        task_queued.UpdateProcessingTime()
        self._UpdateLatestProcessingTime(task_queued)
        return

      task_abandoned = self._tasks_abandoned.get(task_identifier, None)
      if task_abandoned:
        del self._tasks_abandoned[task_identifier]
        self._tasks_processing[task_identifier] = task_abandoned
        logger.debug('Task {0:s} was abandoned, but now processing.'.format(
            task_identifier))

        task_abandoned.UpdateProcessingTime()
        self._UpdateLatestProcessingTime(task_abandoned)
        return

      if task_identifier in self._tasks_pending_merge:
        # No need to update the processing time, as this task is already
        # finished processing and is just waiting for merge.
        return

    # If we get here, we don't know what state the tasks is in, so raise.
    raise KeyError('Status of task {0:s} is unknown.'.format(task_identifier))
