# Plaso static Makefile

# The location of the PyInstaller scripts are hardcoded here
# TODO: change this once PyInstaller supports to be installed
PYINSTALLER=../pyinstaller/pyinstaller.py

prefix=debian/tmp/usr

all: build_log2timeline build_plaso_console build_plaso_information build_psort

build_log2timeline: frontend/log2timeline.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=log2timeline \
	  --paths=../ \
	  $<

build_plaso_console: frontend/plaso_console.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=plaso_console \
	  --paths=../ \
	  $<

build_plaso_information: frontend/plaso_information.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=plaso_information \
	  --paths=../ \
	  $<

build_psort: frontend/psort.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=psort \
	  --paths=../ \
	  $<

clean:
	@rm -rf build/ dist/

install:
	@mkdir -p $(prefix)/lib/plaso
	@install -m 0755 dist/log2timeline/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/log2timeline/log2timeline $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_console/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_console/plaso_console $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_information/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_information/plaso_information $(prefix)/lib/plaso
	@install -m 0755 dist/psort/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/psort/psort $(prefix)/lib/plaso

.py:

.PHONY: all build clean install

