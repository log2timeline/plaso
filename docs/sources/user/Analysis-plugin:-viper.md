Notes on how to use the viper analysis plugin.

## Setting up Viper

The Viper project maintains installation instructions here: https://viper-framework.readthedocs.io/en/latest/installation/index.html

## Running plaso

First run log2timeline to extract events:
```
log2timeline.py timeline.plaso image.raw
```
Note that hashing must be turned on for the viper plugin to work correctly. This is default setting for log2timeline.py.

Next run psort to tag events, then output them:
```
psort.py --analysis viper -o timeline_with_viper_tags.csv timeline.plaso
```
If a file processed by Plaso is present in the viper instance, it will be tagged with `viper_present`. If it's part of a project in viper, it will also be tagged with `viper_project_$PROJECTNAME`.
