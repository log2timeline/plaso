# How to write a tagging rule

This page is intended to give you an introduction into writing rules for
tagging files that can be used by the [tagging analysis plugin](../user/Analysis-plugin-tagging.md).

Tagging rules use [event filters](../user/Event-filters.md).

The following script provides an overview of the attributes event data types
define.

```
PYTHONPATH=. ./utils/export_event_data.py
```

## Contributing changes to tagging rules

Once you have written or changed one or more tagging rules and want to
contribute th changes to the Plaso project. Please follow these steps:

1. If you have not already, please first read the developers guide on [contributing code](Developers-Guide.html#contributing-code).
2. Create a new feature branch.
3. If you are adding a new tagging rule, add it to the most appropriate tagging file. Make sure the tagging rule has brief comment about its purpose.
4. Make sure new or changed tagging rule have the necessary test coverage in https://github.com/log2timeline/plaso/tree/main/tests/data. This is to prevent tagging rules to silently stop working when the Plaso codebase change.
5. Add or update the [tagging rules](../user/Tagging-Rules.md) documentation.

