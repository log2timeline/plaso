@echo off
@rem Script to make sure the executables run after make_dist.bat.

dist\plaso\image_export.exe -h
dist\plaso\log2timeline.exe -h
dist\plaso\pinfo.exe -h
dist\plaso\psort.exe -h
dist\plaso\psteal.exe -h

dist\plaso\log2timeline.exe --troubles
dist\plaso\log2timeline.exe --info

dist\plaso\pinfo.exe -v test_data\pinfo_test.plaso

dist\plaso\log2timeline.exe --status-view=linear dist\test.plaso test_data
