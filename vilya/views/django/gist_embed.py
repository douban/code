# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.http import StreamingHttpResponse
from vilya.libs.template import st
from vilya.config import DOMAIN


EMBED_CSS = """
<link href=\"%s/static/css/highlight.css\" rel=\"stylesheet\">
<link href=\"%s/static/css/embed.css\" rel=\"stylesheet\">
""" % (DOMAIN, DOMAIN)

EMBED_HEAD = "<div id=\"gist%s\" class=\"gist\">"
EMBED_FOOTER = "</div>"

SRC_FORMAT = """
<div class=\"gist-data gist-syntax\">
  <div class=\"gist-file\">
    <div class=\"data\"> %s </div>
    <div class=\"gist-meta\">
      <a href=\"%s/gist/%s/raw/master/%s\" style=\"float:right\">view raw</a>
      <a href=\"%s/gist/%s#%s\" style=\"float:right; margin-right:10px; color:#666;\">%s</a>  # noqa
      <a href=\"%s\">This Gist</a> brought to you by <a href=\"%s\">Code</a>.
    </div>
  </div>
</div>
"""


def index(request, username, id):
    from vilya.libs.text import highlight_code
    from vilya.models.gist import Gist
    gist_id = id

    response = StreamingHttpResponse(content_type='text/javascript')
    response['Content-Disposition'] = 'filename=code_gist_%s.tar.gz' % id
    response['Expires'] = 'Sun, 1 Jan 2006 01:00:00 GMT'
    response['Pragma'] = 'no-cache'
    response['Cache-Control'] = 'must-revalidate, no-cache, private'

    gist = Gist.get(gist_id)
    if not gist_id.isdigit() or not gist:
        response.streaming_content = "document.write('<span style=\"color:red;\">NOT EXIST GIST</span>')"  # noqa
        return response

    html = EMBED_CSS + EMBED_HEAD % gist.id
    for path in gist.files:
        path = path.encode('utf8')
        # TODO: clean this
        src = gist.get_file(path, rev='HEAD')
        src = highlight_code(path, src)
        src = src.replace('"', '\"').replace("'", "\'")
        html += SRC_FORMAT % (src, DOMAIN, gist.id, path, DOMAIN,
                                gist.id, path, path, gist.url, DOMAIN)

    html += EMBED_FOOTER
    html = html.replace('\n', '\\n')
    response.streaming_content = "document.write('%s')" % html
    return response
