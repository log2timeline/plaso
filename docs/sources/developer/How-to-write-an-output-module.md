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
  * GetFieldValues(output_mediator, event, event_data, event_data_stream, event_tag),
    which returns the output field values of an event as a dictionary
  * WriteFieldValues(output_mediator, field_values), which writes the output
    field values of an event
* You may also want to override:
  * Open()
  * Close()
  * GetMissingArguments()
  * WriteFieldValuesOfMACBGroup(output_mediator, macb_group)
  * WriteHeader(output_mediator)
  * WriteFooter()
* The following class attributes indicate what the output module supports:
  * SUPPORTS_ADDITIONAL_FIELDS, the output module supports additional fields,
    for example with `psort.py --additional-fields`
  * SUPPORTS_CUSTOM_FIELDS, the output module supports custom fields, for
    example with `psort.py --custom-fields`
  * WRITES_OUTPUT_FILE, the output module writes to an output file. The path
    of the output file is passed to `Open(path=...)`.

An output module that writes to a text file can subclass
`plaso.output.text_file.TextFileOutputModule`, which sets `WRITES_OUTPUT_FILE`
and implements `Open()`, `Close()`, `WriteLine()` and `WriteText()`. For
example:

```python
"""Output module that writes the data type of every event to a text file."""

from plaso.output import manager
from plaso.output import text_file


class DataTypeOutputModule(text_file.TextFileOutputModule):
    """Output module that writes the data type of every event to a text file."""

    NAME = "data_type"
    DESCRIPTION = "Data type of every event."

    # pylint: disable=unused-argument

    def GetFieldValues(
        self, output_mediator, event, event_data, event_data_stream, event_tag
    ):
        """Retrieves the output field values.

        Args:
          output_mediator (OutputMediator): mediates interactions between output
              modules and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.
          event_tag (EventTag): event tag.

        Returns:
          dict[str, str]: output field values per name.
        """
        return {"data_type": event_data.data_type}

    def WriteFieldValues(self, output_mediator, field_values):
        """Writes field values to the output.

        Args:
          output_mediator (OutputMediator): mediates interactions between output
              modules and other components, such as storage and dfVFS.
          field_values (dict[str, str]): output field values per name.
        """
        self.WriteLine(field_values["data_type"])


manager.OutputManager.RegisterOutput(DataTypeOutputModule)
```

The method signatures are defined in `plaso/output/interface.py` and
`plaso/output/text_file.py`. See `plaso/output/null.py` for a minimal output
module.

If your output module needs command line options, add an arguments helper for
it in `plaso/cli/helpers/`, for example `plaso/cli/helpers/xlsx_output.py`.

## Expand tests

* Add additional tests that test your plugin

`OutputModuleTestCase._CreateOutputMediator()` creates an output mediator to
pass to `GetFieldValues()` and `WriteFieldValues()`. See
`tests/output/null.py` for an example.

## Register classes

* Edit `plaso/output/__init__.py` to import your plugin in the correct
alphabetical order.

## Code review/submit

* Create a PR to have the changes reviewed and merged with the main branch.
