#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""The serializer object interfaces."""

# Since abc does not seem to have an @abc.abstractclassmethod we're using
# @abc.abstractmethod instead and shutting up pylint about:
# E0213: Method should have "self" as first argument.
# pylint: disable-msg=E0213

import abc


class AnalysisReportSerializer(object):
  """Class that implements the analysis report serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an analysis report from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      An analysis report (instance of AnalysisReport).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, analysis_report):
    """Writes an analysis report to serialized form.

    Args:
      analysis_report: an analysis report (instance of AnalysisReport).

    Returns:
      An object containing the serialized form.
    """


class EventContainerSerializer(object):
  """Class that implements the event container serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an event container from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      An event container (instance of EventContainer).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, event_container):
    """Writes an event container to serialized form.

    Args:
      event_container: an event container (instance of EventContainer).

    Returns:
      An object containing the serialized form.
    """


class EventGroupSerializer(object):
  """Class that implements the event group serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an event group from serialized form.

    Args:
      serialized: an group containing the serialized form.

    Returns:
      An event group (instance of EventGroup).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, event_group):
    """Writes an event group to serialized form.

    Args:
      event_group: an event group (instance of EventGroup).

    Returns:
      An group containing the serialized form.
    """


class EventObjectSerializer(object):
  """Class that implements the event object serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an event object from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      An event object (instance of EventObject).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, event_object):
    """Writes an event object to serialized form.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      An object containing the serialized form.
    """


class EventPathBundleSerializer(object):
  """Class that implements the event path bundle serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an event path bundle from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      An event path bundle (instance of EventPathBundle).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, event_path_bundle):
    """Writes an event path bundle to serialized form.

    Args:
      event_path_bundle: an event path bundle (instance of EventPathBundle).

    Returns:
      An object containing the serialized form.
    """


class EventPathSpecSerializer(object):
  """Class that implements the event path specification serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an event path specification from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      An event path specification (instance of EventPathSpec).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, event_path_spec):
    """Writes an event path specification to serialized form.

    Args:
      event_path_spec: an event path specification (instance of EventPathSpec).

    Returns:
      An object containing the serialized form.
    """


class EventTagSerializer(object):
  """Class that implements the event tag serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads an event tag from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      An event tag (instance of EventTag).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, event_tag):
    """Writes an event tag to serialized form.

    Args:
      event_tag: an event tag (instance of EventTag).

    Returns:
      An object containing the serialized form.
    """


class PathFilterSerializer(object):
  """Class that implements the path filter serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads a path filter from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      A path filter (instance of PathFilter).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, path_filter):
    """Writes a path filter to serialized form.

    Args:
      path_filter: a path filter (instance of PathFilter).

    Returns:
      An object containing the serialized form.
    """


class PreprocessObjectSerializer(object):
  """Class that implements the preprocessing object serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads a path filter from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      A preprocessing object (instance of PreprocessObject).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, pre_obj):
    """Writes a preprocessing object to serialized form.

    Args:
      pro_obj: a preprocessing object (instance of PreprocessObject).

    Returns:
      An object containing the serialized form.
    """
