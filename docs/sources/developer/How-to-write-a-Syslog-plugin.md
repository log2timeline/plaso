## Locate/create test data
* Add a test file to the test_data directory

## Create empty files and classes
* plugin file in plaso/parsers/syslog_plugins
  * Create an empty subclass of plaso.parsers.syslog_plugins.interface.SyslogPlugin
  * Register it with the syslog parser by calling SyslogParser.RegisterPlugin
  * Create an empty subclass of SyslogLineEventData
    * Choose an appropriate DATA_TYPE value, starting with 'syslog:'
* plugin test file in tests/parsers/syslog_plugins
* formatter file in plaso/formatters
  * Create an empty subclass of ConditionalEventFormatter
  * Define the DATA_TYPE value to be the same as for your EventData class
* formatter test file in tests/formatters

## Write event data class

* Create a subclass of SyslogLineEventData in the plugin file.
* Define the attributes events produced by your plugin will have.

## Write minimal tests
* Write a test that loads your plugin and parses a file. 
* It will fail initially, but running the test while you're developing your plugin gives you a quick way to see if your code is doing what you expect.
## Develop plugin
* Implement your subclass of plaso.parsers.syslog_plugins.interface.SyslogPlugin
* You'll need to define/overwrite:
  * NAME
  * DESCRIPTION
  * REPORTER
  * MESSAGE_GRAMMARS
## Write the formatter
*  Implement your formatter
## Expand tests
* Add additional tests that test your plugin and formatter
## Register classes
* Edit plaso/parsers/syslog_plugins/__init__.py to import your plugin in the correct alphabetical order.
* Edit plaso/formatters/__init__.py to import your formatter in the correct alphabetical order.
## Code review/submit
