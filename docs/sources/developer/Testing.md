# Testing

Plaso comes with multiple forms of tests:

* unit tests
* end-to-end tests

## Unit tests

The unit tests are intended to detect issues after individual changes (pull
requests). Unit tests are typically small by nature and only test a specific
part of the code.

The unit tests are stored in the `tests` sub directory, in the same parent
directory as the plaso module directory. The unit tests can be run with:

```
python run_tests.py
```

Or if you have tox installed:

```
tox -epy310
```

The unit tests are also run on [GitHub](https://github.com/log2timeline/plaso/actions)
and [AppVeyor](https://ci.appveyor.com/project/log2timeline/plaso) after every
pull request or commit to detect issues early.

## End-to-end tests

The end-to-end tests are intended to test the Plaso tools as a user would run
them. To run the end-to-end tests you'll need:

* the end-to-end test runner script, which is `tests/end-to-end.py`
* end-to-end tests configuration, for example `config/end-to-end.ini`
* location of the reference data, to compare test output against
* location of the result data
* location of the source data

For example, to run the predefined end-to-end tests:

```
PYTHONPATH=. python ./tests/end-to-end.py --debug -c config/end-to-end.ini --references-directory test_reference_data --results-directory test_results --sources-directory test_source_data
```

The predefined end-to-end tests are also run automatically on [GitHub](https://github.com/log2timeline/plaso/actions)
after every commit (code submit).

### End-to-end test configuration

An end-to-end tests configuration file is an INI file where every section
defines a test. The section name is the name of the test and is used in the
names of the files the test creates. For example:

```
[extract_and_output1]
case=extract_and_output
extract_options=--vss_stores=none
output_file=extract_and_output1.log
output_format=dynamic
output_options=--dynamic-time
reference_output_file=test_data/end_to_end/extract_and_output.log
source=test_data/vsstest.qcow2
```

The `case` value defines the test case, which defines the steps of the test
and the values it supports.

Test case | Description
--- | ---
`analyze_and_output` | Runs psort with analysis and output options on an existing storage file.
`extract_and_analyze` | Runs log2timeline, psort with analysis options and psort with output options.
`extract_and_output` | Runs log2timeline, pinfo and psort.
`extract_and_output_with_psteal` | Runs psteal.
`extract_and_tag` | Runs log2timeline, psort with the tagging analysis plugin and psort with output options.
`image_export` | Runs image_export.
`multi_analyze_and_output` | Runs psort twice with different analysis options and then psort with output options, on an existing storage file.
`multi_extract_and_output` | Runs log2timeline on 2 sources, into the same storage file, and then pinfo and psort.

The following values are supported, where not every test case supports
every value:

Value | Description
--- | ---
`source` | Path of the source, relative to the sources directory. The `multi_extract_and_output` test case uses `source1` and `source2` instead.
`source_options` | Options of the source, where `backup` indicates the test should use a copy of the source. Used by the `analyze_and_output` test case.
`extract_options` | Additional log2timeline or psteal options, for example `--parsers=winreg`.
`analysis_options` | psort analysis options, for example `--analysis unique_domains_visited`. The `multi_analyze_and_output` test case uses `analysis_options1` and `analysis_options2` instead.
`output_format` | psort or psteal output format, for example `dynamic`.
`output_options` | Additional psort or psteal output options.
`output_file` | Name of the output file.
`output_filter` | psort event filter.
`export_options` | Additional image_export options.
`custom_formatter_file` | Path of a custom formatter definitions file, relative to the sources directory.
`filter_file` | Path of a collection filter file, relative to the sources directory.
`tagging_file` | Path of a tagging file, relative to the sources directory.
`yara_rules` | Path of a YARA rules file, relative to the sources directory.
`hashes_file` | Name of the file to which the image_export test case writes the hashes of the exported files.
`reference_output_file` | Path of the reference output file, relative to the references directory. If set the output file is compared against it.
`reference_storage_file` | Path of the reference storage file, relative to the references directory. If set the storage file is compared against it with `pinfo.py --compare`.
`reference_hashes_file` | Path of the reference hashes file, relative to the references directory.
`reference_hashes_json_file` | Path of the reference hashes.json file, created by image_export, relative to the references directory.
`logging_options` | Additional logging options, where `%command%` is replaced by the name of the tool and `%results%` by the results directory, for example `--log-file=plaso-out/%command%.log.gz`.
`profiling_options` | Additional profiling options, where `%results%` is replaced by the results directory.

Note that values that contain options are split on spaces and an option in the
form `--option=value` is split into `--option` and `value`. Hence option values
cannot contain spaces.

If the sources or references directory is not specified, paths are relative to
the current working directory. The storage, output and tool output (stdout and
stderr) files of a test are copied to the results directory, which defaults to
the current working directory.

### Running end-to-end tests with Docker

To run end-to-end tests with Docker you'll need:

* Linux with Docker installed
* the end-to-end test Docker script, which is `config/end_to_end/run_tests_with_docker.sh`
* location of the end-to-end tests configurations
* location of the result data
* location of the source data

```
./config/end_to_end/run_tests_with_docker.sh /greendale/configs /greendale/sources /greendale/results
```

