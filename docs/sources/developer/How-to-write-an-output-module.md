# How to write an output module

## Create file and class

* Plugin file in `plaso/output/`
  * Create an empty subclass of [plaso.output.interface.OutputModule](../api/plaso.output.html#plaso.output.interface.OutputModule)
  * Register it with the output module manager by calling
 [OutputManager.RegisterOutput](../api/plaso.output.html#plaso.output.manager.OutputManager.RegisterOutput)
* Test file in `tests/output/`
  * Create an empty subclass of `tests.output.test_lib.OutputModuleTestCase`

## Write minimal tests

* Write a test that loads your output module.
* It will fail initially, but running the test while you're developing your
plugin gives you a quick way to see if your code is doing what you expect.

## Develop plugin

* Implement your subclass of [plaso.output.interface.OutputModule](../api/plaso.output.html#plaso.output.interface.OutputModule)
* You'll need to define/overwrite:
  * NAME
  * DESCRIPTION
  * WriteEventBody
* You may also want to override:
  * Open()
  * Close()
  * GetMissingArguments()
  * WriteHeader()
  * WriteFooter()

## Expand tests

* Add additional tests that test your plugin

## Register classes

* Edit `plaso/output/__init__.py` to import your plugin in the correct
alphabetical order.

## Code review/submit

* Create a PR to have the changes reviewed and merged with the main branch.
