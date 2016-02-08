# -*- coding: utf-8 -*-

from django.http import Http404
from django.http import HttpResponseServerError
from django.http import StreamingHttpResponse


def index(request, username, id, revision, filename):
    from vilya.models.gist import Gist
    gist = Gist.get(id)
    path = filename

    try:
        # TODO: clean this
        text = gist.get_file(path, rev=revision)
    except IOError:
        return HttpResponseServerError()
    if isinstance(text, bool) and text is False:
        raise Http404

    response = StreamingHttpResponse(content_type='text/plain; charset=utf-8')
    response.streaming_content = text.encode('utf-8')
    return response

