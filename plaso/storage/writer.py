"""The storage writer."""

import abc
import collections

from plaso.containers import counts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.storage import reader


class StorageWriter(reader.StorageReader):
    """Storage writer interface."""

    _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
    _CONTAINER_TYPE_ANALYSIS_WARNING = warnings.AnalysisWarning.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT = events.EventObject.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_DATA = events.EventData.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
    _CONTAINER_TYPE_EVENT_TAG = events.EventTag.CONTAINER_TYPE
    _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
    _CONTAINER_TYPE_PREPROCESSING_WARNING = warnings.PreprocessingWarning.CONTAINER_TYPE
    _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE

    # The maximum number of cached event tags
    _MAXIMUM_CACHED_EVENT_TAGS = 32 * 1024

    def __init__(self, storage_type=definitions.STORAGE_TYPE_SESSION):
        """Initializes a storage writer.

        Args:
          storage_type (Optional[str]): storage type.
        """
        super().__init__()
        self._attribute_containers_counter = collections.Counter()
        self._event_tag_per_event_identifier = collections.OrderedDict()
        self._storage_type = storage_type

    def _CacheEventTagByEventIdentifier(self, event_tag, event_identifier):
        """Caches a specific event tag.

        Args:
          event_tag (EventTag): event tag.
          event_identifier (AttributeContainerIdentifier): event identifier.
        """
        if len(self._event_tag_per_event_identifier) >= (
            self._MAXIMUM_CACHED_EVENT_TAGS
        ):
            self._event_tag_per_event_identifier.popitem(last=True)

        lookup_key = event_identifier.CopyToString()

        self._event_tag_per_event_identifier[lookup_key] = event_tag
        self._event_tag_per_event_identifier.move_to_end(lookup_key, last=False)

    def _GetCachedEventTag(self, event_identifier):
        """Retrieves a specific cached event tag.

        Args:
          event_identifier (AttributeContainerIdentifier): event identifier.

        Returns:
          EventTag: event tag or None if not available.

        Raises:
          OSError: when there is an error querying the storage file.
        """
        lookup_key = event_identifier.CopyToString()

        event_tag = self._event_tag_per_event_identifier.get(lookup_key)
        if not event_tag:
            generator = self._store.GetAttributeContainers(
                self._CONTAINER_TYPE_EVENT_TAG,
                filter_expression=f'_event_identifier == "{lookup_key:s}"',
            )

            existing_event_tags = list(generator)
            if len(existing_event_tags) == 1:
                event_tag = existing_event_tags[0]

                if len(self._event_tag_per_event_identifier) >= (
                    self._MAXIMUM_CACHED_EVENT_TAGS
                ):
                    self._event_tag_per_event_identifier.popitem(last=True)

                self._event_tag_per_event_identifier[lookup_key] = event_tag

        if event_tag:
            self._event_tag_per_event_identifier.move_to_end(lookup_key, last=False)

        return event_tag

    def _RaiseIfNotWritable(self):
        """Raises if the storage writer is not writable.

        Raises:
          OSError: when the storage writer is closed.
        """
        if not self._store:
            raise OSError("Unable to write to closed storage writer.")

    def AddAttributeContainer(self, container):
        """Adds an attribute container.

        Args:
          container (AttributeContainer): attribute container.

        Raises:
          OSError: when the storage writer is closed.
        """
        self._RaiseIfNotWritable()

        self._store.AddAttributeContainer(container)

        self._attribute_containers_counter[container.CONTAINER_TYPE] += 1

    def AddOrUpdateEventTag(self, event_tag):
        """Adds a new or updates an existing event tag.

        Args:
          event_tag (EventTag): event tag.

        Raises:
          OSError: when the storage writer is closed.
        """
        self._RaiseIfNotWritable()

        event_identifier = event_tag.GetEventIdentifier()

        existing_event_tag = self._GetCachedEventTag(event_identifier)
        if not existing_event_tag:
            self.AddAttributeContainer(event_tag)

            self._CacheEventTagByEventIdentifier(event_tag, event_identifier)

        else:
            if not set(existing_event_tag.labels).issubset(event_tag.labels):
                # No need to update the storage if all the labels are already set.
                existing_event_tag.AddLabels(event_tag.labels)
                self._store.UpdateAttributeContainer(existing_event_tag)

            if self._storage_type == definitions.STORAGE_TYPE_TASK:
                self._attribute_containers_counter[self._CONTAINER_TYPE_EVENT_TAG] += 1

    def Close(self):
        """Closes the storage writer.

        Raises:
          OSError: when the storage writer is closed.
        """
        self._RaiseIfNotWritable()

        self._store.Close()
        self._store = None

    @abc.abstractmethod
    def GetFirstWrittenEventData(self):
        """Retrieves the first event data that was written after open.

        Using GetFirstWrittenEventData and GetNextWrittenEventData newly
        added event data can be retrieved in order of addition.

        Returns:
          EventData: event data or None if there are no newly written ones.
        """

    @abc.abstractmethod
    def GetNextWrittenEventData(self):
        """Retrieves the next event data that was written after open.

        Returns:
          EventData: event data or None if there are no newly written ones.
        """

    @abc.abstractmethod
    def GetFirstWrittenEventSource(self):
        """Retrieves the first event source that was written after open.

        Using GetFirstWrittenEventSource and GetNextWrittenEventSource newly
        added event sources can be retrieved in order of addition.

        Returns:
          EventSource: event source or None if there are no newly written ones.
        """

    @abc.abstractmethod
    def GetNextWrittenEventSource(self):
        """Retrieves the next event source that was written after open.

        Returns:
          EventSource: event source or None if there are no newly written ones.
        """

    @abc.abstractmethod
    def Open(self, **kwargs):
        """Opens the storage writer."""

    def UpdateAttributeContainer(self, container):
        """Updates an existing attribute container.

        Args:
          container (AttributeContainer): attribute container.

        Raises:
          OSError: when the storage writer is closed.
        """
        self._RaiseIfNotWritable()

        self._store.UpdateAttributeContainer(container)

    def UpdateDataTypesCounter(self, stored_data_types_counter, data_types_counter):
        """Updates the data types counter.

        Args:
          stored_data_types_counter (collections.Counter): the stored data types
              counter.
          data_types_counter (collections.Counter): the data types counter with
              additional values.
        """
        for key, value in data_types_counter.items():
            data_type_count = stored_data_types_counter.get(key, None)
            if data_type_count:
                data_type_count.number_of_events += value
                self.UpdateAttributeContainer(data_type_count)
            else:
                data_type_count = counts.DataTypeCount(name=key, number_of_events=value)
                data_types_counter[key] = data_type_count
                self.AddAttributeContainer(data_type_count)

    def UpdateEventLabelsCounter(
        self, stored_event_labels_counter, event_labels_counter
    ):
        """Updates the event labels counter.

        Args:
          stored_event_labels_counter (collections.Counter): the stored event labels
              counter.
          event_labels_counter (collections.Counter): the event labels counter with
              additional values.
        """
        for key, value in event_labels_counter.items():
            parser_count = stored_event_labels_counter.get(key)
            if parser_count:
                parser_count.number_of_events += value
                self.UpdateAttributeContainer(parser_count)
            else:
                parser_count = counts.ParserCount(name=key, number_of_events=value)
                event_labels_counter[key] = parser_count
                self.AddAttributeContainer(parser_count)

    def UpdateParsersCounter(self, stored_parsers_counter, parsers_counter):
        """Updates the parsers counter.

        Args:
          stored_parsers_counter (collections.Counter): the stored parsers counter.
          parsers_counter (collections.Counter): the parsers counter with additional
              values.
        """
        for key, value in parsers_counter.items():
            parser_count = stored_parsers_counter.get(key)
            if parser_count:
                parser_count.number_of_events += value
                self.UpdateAttributeContainer(parser_count)
            else:
                parser_count = counts.ParserCount(name=key, number_of_events=value)
                parsers_counter[key] = parser_count
                self.AddAttributeContainer(parser_count)
