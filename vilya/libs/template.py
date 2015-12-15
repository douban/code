# coding: utf-8

import os
from os.path import join
import logging
logging.getLogger().setLevel(logging.DEBUG)

from mako import exceptions
from mako.lookup import TemplateLookup
from vilya.libs.permdir import get_tmpdir
from vilya.libs.import_obj import import_obj
from vilya.config import CODE_DIR, MAKO_FS_CHECK, DEVELOP_MODE

import vilya.libs.mako_cache  # noqa


MAKO_CACHE_DIR = join(get_tmpdir(), "tmp_mako_0606", "mako_cache")

c = import_obj("c")
request = import_obj("request")

code_templates = TemplateLookup(
    directories=CODE_DIR + '/templates',
    module_directory=MAKO_CACHE_DIR,
    input_encoding='utf8',
    output_encoding='utf8',
    encoding_errors='ignore',
    default_filters=['h'],
    filesystem_checks=MAKO_FS_CHECK,
    cache_enabled=True,
    cache_impl='mccache',
    imports=["from vilya.libs.tplhelpers import static"]
)


def serve_template(uri, **kwargs):
    _t = code_templates.get_template(str(uri))
    if 'self' in kwargs:
        kwargs.pop('self')
    try:
        return _t.render(c=c._real, **kwargs)

    except Exception, err:
        logging.debug("Mako error in %s: %s" % (uri, err))
        if DEVELOP_MODE:
            raise
        logging.debug(exceptions.text_error_template().render())

        if os.environ.get('DAE_ENV') == 'SDK':
            import traceback
            traceback.print_exc()
            return exceptions.text_error_template().render(full=True)

        return exceptions.text_error_template().render(full=True)

st = serve_template
