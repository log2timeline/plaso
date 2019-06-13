# Using psteal.py

**psteal** (Plaso SýndarheimsTímalína sem Er ALgjörlega sjálfvirk) is a command line tool which uses [log2timeline](Using-log2timeline.md) and [psort](Using-psort.md) engines to extract and process [events](Scribbles-about-events.md#what-is-an-event) in one go.

It is a quick shortcut to the "*kitchen sink*" approach and only supports a very limited subset of options the above tools provide.

## Usage

To see a list of all available parameters you can pass to psort use ``-h`` or ``--help``.

Psteal requires at least a source evidence, specified with ``--source`` and a output with ``-w``. For example:

`psteal.py --source ~/cases/greendale/registrar.dd -w /tmp/registrar.csv` will produce a csv file containing all the events from an image, using log2timeline and psort defaults options.

The intermediary Plaso storage file will be created in the local directory. In the previous example it will be named ``<TIMESTAMP>-registrar.dd.plaso``.
This can be used for further processing with Psort or [Timesketch](https://github.com/google/timesketch).

## Options

Psteal purposefully supports only a limited subset of options from both [log2timeline](Using-log2timeline.md) and [psort](Using-psort.md) tools.
Please refer to their respective documentations for more information, for example for help regarding the [output formats](Using-psort.md#Output).

If your use case requires specific options to either log2timeline or psort, please use both command line tools separately.
