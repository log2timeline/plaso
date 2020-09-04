FROM python:3.8-windowsservercore

WORKDIR /usr/src/app

RUN python -m pip install msvc-runtime pywin32 WMI

RUN python -m pip download https://github.com/log2timeline/l2tdevtools/archive/main.zip
RUN powershell.exe -Command Expand-Archive main.zip -DestinationPath .

WORKDIR /usr/src/app/l2tdevtools-main
RUN mkdir dependencies
ENV PYTHONPATH=.
RUN python tools\update.py --download-directory dependencies --preset plaso

WORKDIR /usr/src/app
