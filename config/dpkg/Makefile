# Plaso static Makefile

# The location of the PyInstaller scripts are hardcoded here
# TODO: change this once PyInstaller supports to be installed
PYINSTALLER=../pyinstaller/pyinstaller.py

prefix=debian/tmp/usr

all: build_log2timeline build_pinfo build_plasm build_pprof build_preg build_pshell build_psort build_image_export

build_image_export: tools/image_export.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=image_export \
	  --paths=./ \
	  $<

build_log2timeline: plaso/frontend/log2timeline.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=log2timeline \
	  --paths=./ \
	  $<

build_pinfo: plaso/frontend/pinfo.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=pinfo \
	  --paths=./ \
	  $<

build_plasm: plaso/frontend/plasm.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=plasm \
	  --paths=./ \
	  $<

build_pprof: plaso/frontend/pprof.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=pprof \
	  --paths=./ \
	  $<

build_preg: plaso/frontend/preg.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=preg \
	  --paths=./ \
	  $<

build_pshell: plaso/frontend/pshell.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=pshell \
	  --paths=./ \
	  $<

build_psort: plaso/frontend/psort.py
	$(PYINSTALLER) \
	  --onedir \
	  --console \
	  --name=psort \
	  --paths=./ \
	  $<

clean:
	@rm -rf build/ dist/

install:
	@mkdir -p $(prefix)/lib/plaso
	@install -m 0755 dist/image_export/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/image_export/image_export $(prefix)/lib/plaso
	@install -m 0755 dist/log2timeline/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/log2timeline/log2timeline $(prefix)/lib/plaso
	@install -m 0755 dist/pinfo/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/pinfo/pinfo $(prefix)/lib/plaso
	@install -m 0755 dist/plasm/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/plasm/plasm $(prefix)/lib/plaso
	@install -m 0755 dist/pprof/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/pprof/pprof $(prefix)/lib/plaso
	@install -m 0755 dist/preg/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/preg/preg $(prefix)/lib/plaso
	@install -m 0755 dist/pshell/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/pshell/pshell $(prefix)/lib/plaso
	@install -m 0755 dist/psort/*.* $(prefix)/lib/plaso
	@install -m 0755 dist/psort/psort $(prefix)/lib/plaso

.py:

.PHONY: all build clean install

