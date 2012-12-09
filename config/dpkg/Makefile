# Plaso static Makefile

# The location of the PyInstaller scripts are hardcoded here
# TODO: change this once PyInstaller supports to be installed
PYINSTALLER=../pyinstaller/pyinstaller.py
UTILS_MAKESPEC=../pyinstaller/utils/Makespec.py
UTILS_BUILD=../pyinstaller/utils/Build.py

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
	$(UTILS_MAKESPEC) \
	  --onedir \
	  --console \
	  --name=plaso_console \
	  --paths=../ \
	  $<
	sed "/hookspath=None)/a\
a.datas += [\n\
  ('IPython/config/profile/README_STARTUP',\n\
   '/usr/share/pyshared/IPython/config/profile/README_STARTUP',\n\
   'DATA')]" -i plaso_console.spec
	$(UTILS_BUILD) \
	  plaso_console.spec

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
	@mkdir -p $(prefix)/lib/plaso/IPython/config/profile/
	@install -m 0755 dist/log2timeline/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/log2timeline/log2timeline $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_console/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_console/plaso_console $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_console/IPython/config/profile/README_STARTUP $(prefix)/lib/plaso/IPython/config/profile/
	@install -m 0755 dist/plaso_information/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/plaso_information/plaso_information $(prefix)/lib/plaso
	@install -m 0755 dist/psort/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/psort/psort $(prefix)/lib/plaso

.py:

.PHONY: all build clean install

