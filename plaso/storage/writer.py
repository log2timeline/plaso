# -*- coding: utf-8 -*-
"""The storage writer objects."""

from plaso.engine import plaso_queue
from plaso.lib import definitions


class StorageWriter(plaso_queue.ItemQueueConsumer):
  """Class that defines the storage writer interface."""

  # pylint: disable=abstract-method
  # Have pylint ignore that we are not overriding _ConsumeItem.

  def __init__(self, event_object_queue):
    """Initializes a storage writer object.

    Args:
      event_object_queue: the event object queue (instance of Queue).
    """
    super(StorageWriter, self).__init__(event_object_queue)

    # Attributes that contain the current status of the storage writer.
    self._status = definitions.PROCESSING_STATUS_INITIALIZED

    # Attributes for profiling.
    self._enable_profiling = False
    self._profiling_type = u'all'

  def _Close(self):
    """Closes the storage writer."""
    return

  def _Open(self):
    """Opens the storage writer."""
    return

  def GetStatus(self):
    """Returns a dictionary containing the status."""
    return {
        u'number_of_events': self.number_of_consumed_items,
        u'processing_status': self._status,
        u'type': definitions.PROCESS_TYPE_STORAGE_WRITER}

  def SetEnableProfiling(self, enable_profiling, profiling_type=u'all'):
    """Enables or disables profiling.

    Args:
      enable_profiling: boolean value to indicate if profiling should
                        be enabled.
      profiling_type: optional profiling type.
    """
    self._enable_profiling = enable_profiling
    self._profiling_type = profiling_type

  def WriteEventObjects(self):
    """Writes the event objects that are pushed on the queue."""
    self._status = definitions.PROCESSING_STATUS_RUNNING

    self._Open()
    self.ConsumeItems()
    self._Close()

    self._status = definitions.PROCESSING_STATUS_COMPLETED


class BypassStorageWriter(StorageWriter):
  """Class that implements a bypass storage writer object.

  The bypass storage writer allows to directly pass event objects to
  an output module instead of writing them first to a file storage file.
  """

  def __init__(
      self, event_object_queue, output_file, preprocessing_object,
      output_module_string=u'l2tcsv'):
    """Initializes the bypass storage writer.

    Args:
      event_object_queue: an event object queue (instance of Queue).
      output_file: a string containing path to the output file.
      preprocessing_object: a preprocessing object (instance of
                            PreprocessObject).
      output_module_string: optional string containing the name of the output
                            module.
    """
    super(BypassStorageWriter, self).__init__(event_object_queue)
    self._output_file = output_file
    self._output_module = None
    self._output_module_string = output_module_string
    self._preprocessing_object = preprocessing_object
    self._preprocessing_object.store_range = (1, 1)

  def _Close(self):
    """Closes the storage writer."""
    # TODO: Re-enable this when storage library has been split up.
    # Also update code to use NewOutputModule().
    # pylint: disable=pointless-string-statement
    """
    self._output_module.End()
    """

  def _ConsumeItem(self, event_object, **unused_kwargs):
    """Consumes an item callback for ConsumeItems."""
    # Set the store number and index to default values since they are not used.
    event_object.store_number = 1
    event_object.store_index = -1

    self._output_module.WriteEvent(event_object)

  def _Open(self):
    """Opens the storage writer."""
    # TODO: Re-enable this when storage library has been split up.
    # Also update code to use NewOutputModule().
    # pylint: disable=pointless-string-statement
    """
    output_class = output_manager.OutputManager.GetOutputClass(
        self._output_module_string)
    if not output_class:
      output_class = output_manager.OutputManager.GetOutputClass('l2tcsv')
    self._output_module = output_class(
        self, formatter_mediator, filehandle=self._output_file,
        config=self._preprocessing_object)

    self._output_module.Start()
    """

  # Typically you will have a storage object that has this function,
  # as in you can call store.GetStorageInformation and that will read
  # the information from the store. However in this case we are not
  # actually using a storage file, we are using a "storage bypass" file,
  # and since some parts of the codebase expect this to be set (an
  # interface if you want to call it that way, although the storage
  # has not been abstracted into an interface, perhaps it should be)
  # then this has to be set. And the interface behavior is to return
  # a list of all available storage information objects (or all
  # preprocessing objects stored in the storage file)
  def GetStorageInformation(self):
    """Return information about the storage object (used by output modules)."""
    return [self._preprocessing_object]
