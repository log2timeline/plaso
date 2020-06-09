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
  * NAME
  * ExamineEvent()
  * CompileReport()
* You may also want to override:
  * URLS
  * ENABLE_IN_EXTRACTION, if your plugin is eligible to run while Plaso is
extracting events.

## Expand tests
* Add additional tests that test your plugin

## Register classes
* Edit `plaso/analysis/__init__.py` to import your plugin in the correct
 alphabetical order.

## Code review/submit
