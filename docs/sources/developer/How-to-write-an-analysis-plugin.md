# How to write an analysis plugin

## Create file and class
* Plugin file in `plaso/analysis/`
  * Create an empty subclass of [AnalysisPlugin](../api/plaso.analysis.html#plaso.analysis.interface.AnalysisPlugin)
  * Register it with the analysis plugin by calling
   [AnalysisPluginManager.RegisterPlugin](../api/plaso.analysis.html#plaso.analysis.manager.AnalysisPluginManager.RegisterPlugin)
* Test file in `tests/analysis/`
  * Create an empty subclass of `tests.analysis.test_lib.AnalysisPluginTestCase`

## Write minimal tests
* Write a test that loads your plugin
* It will fail initially, but running the test while you're developing your
plugin gives you a quick way to see if your code is doing what you expect.

## Develop plugin
* Implement your subclass of [AnalysisPlugin](../api/plaso.analysis.html#plaso.analysis.interface.AnalysisPlugin)
* You'll need to define/override:
  * NAME, a short and unique name of the plugin, which is used to select the
    plugin, for example with `psort.py --analysis`
  * ExamineEvent(analysis_mediator, event, event_data, event_data_stream), which
    is called for every event to analyze
* You may also want to override:
  * CompileReport(analysis_mediator), which is called after every event has
    been examined. The default implementation returns an analysis report that
    contains the values of the `self._analysis_counter` counter, so you only
    need to override it if your plugin reports additional information.

To tag an event, create an event tag with `self._CreateEventTag(event, labels)`
and pass it to `analysis_mediator.ProduceEventTag(event_tag)`.

For example a plugin that counts the events per data type:

```python
"""Analysis plugin that counts events per data type."""

from plaso.analysis import interface
from plaso.analysis import manager


class DataTypesAnalysisPlugin(interface.AnalysisPlugin):
    """Analysis plugin that counts events per data type."""

    NAME = "data_types"

    # pylint: disable=unused-argument
    def ExamineEvent(self, analysis_mediator, event, event_data, event_data_stream):
        """Analyzes an event.

        Args:
          analysis_mediator (AnalysisMediator): mediates interactions between
              analysis plugins and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.
        """
        self._analysis_counter[event_data.data_type] += 1


manager.AnalysisPluginManager.RegisterPlugin(DataTypesAnalysisPlugin)
```

The method signatures are defined in `plaso/analysis/interface.py`. See
`plaso/analysis/unique_domains_visited.py` for a complete plugin.

If your plugin needs command line options, add an arguments helper for it in
`plaso/cli/helpers/`, for example `plaso/cli/helpers/tagging_analysis.py`.

## Expand tests
* Add additional tests that test your plugin

`AnalysisPluginTestCase._AnalyzeEvents()` runs a plugin on events that are
created from a list of event values and returns a storage writer that contains
the analysis report, for example:

```python
    def testExamineEventAndCompileReport(self):
        """Tests the ExamineEvent and CompileReport functions."""
        plugin = data_types.DataTypesAnalysisPlugin()
        storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

        analysis_report = storage_writer.GetAttributeContainerByIndex(
            reports.AnalysisReport.CONTAINER_TYPE, 0
        )
        self.assertIsNotNone(analysis_report)
```

## Register classes
* Edit `plaso/analysis/__init__.py` to import your plugin in the correct
 alphabetical order.

## Code review/submit

* Create a PR to have the changes reviewed and merged with the main branch.
