nothing:
	@echo "Better make nothing be default"

ctags:
	@ctags -R --exclude=dist --exclude=venv --exclude=permdir --exclude=tmpdir --exclude=node_modules

clean_pyc:
	@find . -type f -name '*.pyc' -delete;

pylint:
	@pylint --errors-only --reports=n --include-ids=y --output-format=parseable  --ignore=tracplugs active_stubs/ libs/ models/ static/ stubs/ tasks/ tests/ tools/ views/

web: startcache startweb
	@echo go web: http://localhost:8000/

startweb:
	exec gunicorn -k gevent -b 0.0.0.0:8000 app:app

startcache:
	exec memcached -d -u nobody -l 127.0.0.1 -p 11311 -U 0
