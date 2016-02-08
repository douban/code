# -*- coding: utf-8 -*-


# TODO(xutao) remove quixote middleware
# FIXME(xutao) remove compatibility for quixote

class QuixoteMiddleware(object):

    def process_request(self, request):
        # FIXME(xutao) remove get_header
        if not hasattr(request, 'get_header'):
            def get_header(name):
                return request.META.get(name)
            request.get_header = get_header

        if not hasattr(request, 'get_path'):
            def get_path(n=0):
                path_info = request.environ.get('PATH_INFO', '')
                path = request.environ['SCRIPT_NAME'] + path_info
                if n == 0:
                    return path
                else:
                    path_comps = path.split('/')
                    if abs(n) > len(path_comps)-1:
                        raise ValueError, "n=%d too big for path '%s'" % (n, path)
                    if n > 0:
                        return '/'.join(path_comps[:-n])
                    elif n < 0:
                        return '/'.join(path_comps[:-n+1])
                    else:
                        assert 0, "Unexpected value for n (%s)" % n
            request.get_path = get_path

        if not hasattr(request, 'is_mobile'):
            from vilya.views.util import is_mobile_device
            request.is_mobile = is_mobile_device(request)

        if not hasattr(request, 'url'):
            request.url = request.get_path()
