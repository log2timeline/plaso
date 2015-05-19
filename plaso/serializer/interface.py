# -*- coding: utf-8 -*-
"""The serializer object interfaces."""

# Since abc does not seem to have an @abc.abstractclassmethod we're using
# @abc.abstractmethod instead and shutting up pylint about:
# E0213: Method should have "self" as first argument.
# pylint: disable=no-self-argument

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


class CollectionInformationObjectSerializer(object):
  """Class that implements the collection information serializer interface."""

  @abc.abstractmethod
  def ReadSerialized(cls, serialized):
    """Reads a path filter from serialized form.

    Args:
      serialized: an object containing the serialized form.

    Returns:
      A collection information object (instance of CollectionInformation).
    """

  @abc.abstractmethod
  def WriteSerialized(cls, collection_information_object):
    """Writes a collection information object to serialized form.

    Args:
      collection_information_object: a collection information object (instance
                                     of CollectionInformation).

    Returns:
      An object containing the serialized form.
    """
