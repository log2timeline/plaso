@echo off
@rem Script to make sure the executables run after make_dist.bat.

dist\plaso\image_export.exe -h
dist\plaso\log2timeline.exe --info
dist\plaso\pinfo.exe -v test_data\psort_test.json.plaso
dist\plaso\psort.exe

dist\plaso\log2timeline.exe dist\test.plaso test_data

