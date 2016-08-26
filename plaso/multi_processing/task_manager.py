# -*- coding: utf-8 -*-
"""The task manager."""

import collections
import time

from plaso.containers import tasks


class TaskManager(object):
  """Class that manages tasks and tracks their completion and status."""

  # Consider a task inactive after 5 minutes of no activity.
  _TASK_INACTIVE_TIME = 5 * 60 * 1000000

  def __init__(self, maximum_number_of_tasks=0):
    """Initializes a task manager object.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
    """
    super(TaskManager, self).__init__()
    self._abandoned_tasks = {}
    self._active_tasks = {}
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._scheduled_tasks = {}
    self._tasks_pending_merge = collections.OrderedDict()

  def CompleteTask(self, task_identifier):
    """Completes a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not scheduled.
    """
    if task_identifier not in self._scheduled_tasks:
      raise KeyError(u'Task not scheduled')

    del self._active_tasks[task_identifier]
    del self._scheduled_tasks[task_identifier]

    if task_identifier in self._tasks_pending_merge:
      del self._tasks_pending_merge

  # TODO: add support for task types.
  def CreateTask(self, session_identifier):
    """Creates a task.

    Args:
      session_identifier (str): the identifier of the session the task is
          part of.

    Returns:
      Task: task attribute container.
    """
    task = tasks.Task(session_identifier)
    self._active_tasks[task.identifier] = task
    return task

  def GetAbandonedTasks(self):
    """Retrieves all abandoned tasks.

    Returns:
      list[task]: task.
    """
    return self._abandoned_tasks.values()

  def GetScheduledTaskIdentifiers(self):
    """Retrieves all scheduled task identifiers.

    Returns:
      list[str]: unique identifiers of the tasks.
    """
    return self._scheduled_tasks.keys()

  def HasScheduledTasks(self):
    """Determines if there are scheduled tasks.

    A task will be abandoned if it last update exceeds the inactive time.

    Returns:
      bool: True if there are scheduled active tasks.
    """
    if not self._scheduled_tasks:
      return False

    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

    has_active_tasks = False
    for task_identifier, last_update in iter(self._scheduled_tasks.items()):
      if last_update > inactive_time:
        has_active_tasks = True
      else:
        del self._scheduled_tasks[task_identifier]
        task = self._active_tasks[task_identifier]
        self._abandoned_tasks[task_identifier] = task
        del self._active_tasks[task_identifier]

    return has_active_tasks

  def GetPendingMerge(self):
    """Retrieves the first task that is pending merge.

    Returns:
      str: unique identifier of the task or None.
    """
    if not self._tasks_pending_merge:
      return

    _, task_identifier = self._tasks_pending_merge.popitem(last=False)
    return task_identifier

  def IsPendingMerge(self, task_identifier):
    """Determines if a task is makred as pending merge.

    Args:
      task_identifier (str): unique identifier of the task.

    Returns:
      bool: True if the task is pending for merge.
    """
    if task_identifier not in self._tasks_pending_merge:
      return False

    # Make sure tasks waiting to be merged are not considered idle when
    # not yet merged.
    self.UpdateTask(task_identifier)

    return True

  def MarkAsPendingMerge(self, task_identifier):
    """Marks a task as pending merge.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task was not schduled.
    """
    self._tasks_pending_merge[task_identifier] = task_identifier
    self.UpdateTask(task_identifier)

  def RescheduleTask(self, task_identifier):
    """Reschedules a previous abandoned task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task was not abandoned.
    """
    if task_identifier not in self._abandoned_tasks:
      raise KeyError(u'Task not abandoned')

    task = self._abandoned_tasks[task_identifier]
    self._active_tasks[task_identifier] = task
    del self._abandoned_tasks[task_identifier]

    self._scheduled_tasks[task_identifier] = int(time.time() * 1000000)

  def ScheduleTask(self, task_identifier):
    """Schedules a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is already scheduled.
    """
    if task_identifier in self._scheduled_tasks:
      raise KeyError(u'Task already scheduled')

    # TODO: add check for maximum_number_of_tasks.
    self._scheduled_tasks[task_identifier] = int(time.time() * 1000000)

  def UpdateTask(self, task_identifier):
    """Updates a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not scheduled.
    """
    if task_identifier not in self._scheduled_tasks:
      raise KeyError(u'Task not scheduled')

    self._scheduled_tasks[task_identifier] = int(time.time() * 1000000)
