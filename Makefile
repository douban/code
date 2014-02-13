nothing:
	@echo "Better make nothing be default"

ctags:
	@ctags -R --exclude=dist --exclude=venv --exclude=permdir --exclude=tmpdir --exclude=node_modules

clean_pyc:
	@find . -type f -name '*.pyc' -delete;

pylint:
	@pylint --errors-only --reports=n --include-ids=y --output-format=parseable  --ignore=tracplugs active_stubs/ libs/ models/ static/ stubs/ tasks/ tests/ tools/ views/

