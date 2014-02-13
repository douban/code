#!/usr/bin/env python
'''
Module provides WSGI-based methods for handling HTTP Get and Post requests that
are specific only to git-http-backend's Smart HTTP protocol.

See __version__ statement below for indication of what version of Git's
Smart HTTP server this backend is (designed to be) compatible with.

Copyright (c) 2010  Daniel Dotsenko <dotsa@hotmail.com>
Selected, specifically marked so classes are also
  Copyright (C) 2006 Luke Arno - http://lukearno.com/

This file is part of git_http_backend.py Project.

git_http_backend.py Project is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 2.1 of the License, or
(at your option) any later version.

git_http_backend.py Project is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with git_http_backend.py Project.  If not, see <http://www.gnu.org/licenses/>.
'''
import io
import os
import sys

import subprocess
from code.libs import subprocessio

import tempfile
from wsgiref.headers import Headers

# needed for WSGI Selector
import re
import urlparse
from collections import defaultdict

# needed for static content server
import time
import email.utils
import mimetypes
mimetypes.add_type('application/x-git-packed-objects-toc','.idx')
mimetypes.add_type('application/x-git-packed-objects','.pack')

from cStringIO import StringIO
import gzip

__version__=(1,7,0,4) # the number has no significance for this code's functionality.
# The number means "I was looking at sources of that version of Git while coding"

class BaseWSGIClass(object):
    bufsize = 65536
    gzip_response = False
    canned_collection = {
        '304': '304 Not Modified',
        'not_modified': '304 Not Modified',
        '301': '301 Moved Permanently',
        'moved': '301 Moved Permanently',
        '400':'400 Bad request',
        'bad_request':'400 Bad request',
        '401':'401 Access denied',
        'access_denied':'401 Access denied',
        '401.4': '401.4 Authorization failed by filter',
        '403':'403 Forbidden',
        'forbidden':'403 Forbidden',
        '404': "404 Not Found",
        'not_found': "404 Not Found",
        '405': "405 Method Not Allowed",
        'method_not_allowed': "405 Method Not Allowed",
        '417':'417 Execution failed',
        'execution_failed':'417 Execution failed',
        '200': "200 OK",
        '501': "501 Not Implemented",
        'not_implemented': "501 Not Implemented"
    }

    def canned_handlers(self, environ, start_response, code = '200', headers = []):
        '''
        We convert an error code into
        certain action over start_response and return a WSGI-compliant payload.
        '''
        headerbase = [('Content-Type', 'text/plain')]
        if headers:
            hObj = Headers(headerbase)
            for header in headers:
                hObj[header[0]] = '; '.join(header[1:])
        start_response(self.canned_collection[code], headerbase)
        return ['']

    def package_response(self, outIO, environ, start_response, headers = []):

        newheaders = headers
        headers = [('Content-type', 'application/octet-stream')] # my understanding of spec. If unknown = binary
        headersIface = Headers(headers)

        for header in newheaders:
            headersIface[header[0]] = '; '.join(header[1:])

        if hasattr(outIO,'fileno') and 'wsgi.file_wrapper' in environ:
            outIO.seek(0)
            retobj = environ['wsgi.file_wrapper']( outIO, self.bufsize )
        elif hasattr(outIO,'read'):
            outIO.seek(0)
            retobj = iter( lambda: outIO.read(self.bufsize), '' )
        else:
            retobj = outIO
        start_response("200 OK", headers)
        return retobj

class WSGIHandlerSelector(BaseWSGIClass):
    """
    WSGI middleware for URL paths and HTTP method based delegation.

    This middleware is commonly called a "selector" or "router."

    Features:

    Regex-based patterns:
    Normally these are implemented as meta-url-language-to-regex
    translators, where you describe a URI matching pattern in
    URI-looking way, with regex-like pattern group name areas.
    These later are converted to plain regex by the selector's code.
    Since you need to learn that meta-URI-matching-language and
    have the usual routers translate those to regex, I have decided
    to cut out the middle-man and just define the URI patterns in
    regex from the start.
    This way a WSGI app programmer needs to learn only one meta-URI-matching
    language - standard Python regex. Thus, the insanity should stop here.

    Support for matching based on HTTP verb:
    Want to handle POSTs and GETs on the same URI by different wsgi app? Sure!

    Support for routing based on URI query parameters:
    Want "host/app?special_arg=value" to be routed to different wsgi app
    compared to "host/app?other_arg=value" or "host/app"? Sure!

    See documentation for .add() method for examples.

    Based on Selector from http://lukearno.com/projects/selector/

    Copyright (c) 2010 Daniel Dotsenko <dotsa@hotmail.com>
    Copyright (C) 2006 Luke Arno - http://lukearno.com/
    """

    def __init__(self, WSGI_env_key = 'WSGIHandlerSelector'):
        """
        WSGIHandlerSelector instance initializer.

        WSGIHandlerSelector(WSGI_env_key = 'WSGIHandlerSelector')

        Inputs:
         WSGI_env_key (optional)
          name of the key selector injects into WSGI's environ.
          The key will be the base for other dicts, like .matches - the key-value pairs of
          name-matchedtext matched groups. Defaults to 'WSGIHandlerSelector'
        """
        self.mappings = []
        self.WSGI_env_key = WSGI_env_key

    def add(self, path, default_handler = None, **http_methods):
        """
        Add a selector mapping.

        add(path, default_handler, **named_handlers)

        Adding order is important. Firt added = first matched.
        If you want to hand special case URI handled by one app and shorter
        version of the same regex string by anoter app,
        .add() special case first.

        Inputs:
         path - A regex string. We will compile it.
          Highly recommend using grouping of type: "(?P<groupname>.+)"
          These will be exposed to WSGI app through environment key
          per http://www.wsgi.org/wsgi/Specifications/routing_args

         default_handler - (optional) A pointer to the function / iterable
          class instance that will handle ALL HTTP methods (verbs)

         **named_handlers - (optional) An unlimited list of named args or
          an unpacked dict of handlers allocated to handle specific HTTP
          methods (HTTP verbs). See "Examples" below.

        Matched named method handlers override default handler.

        If neither default_handler nor named_handlers point to any methods,
        "Method not implemented" is returned for the requests on this URI.

        Examples:
        selectorInstance.add('^(?P<working_path>.*)$',generic_handler,
                              POST=post_handler, HEAD=head_handler)

        custom_assembled_dict = {'GET':wsgi_app_a,'POST':wsgi_app_b}:
        ## note the unpacking - "**" - of the dict in this case.
        selectorInstance.add('^(?P<working_path>.*)$', **custom_assembled_dict)


        If the string contains '\?' (escaped ?, which translates to '?' in
        non-regex strings) we understand that as "do regex matching on
        QUERY_PATH + '?' + QUERY_STRING"

        When lookup matches are met, results are injected into
        environ['wsgiorg.routing_args'] per
        http://www.wsgi.org/wsgi/Specifications/routing_args
        """
        if default_handler:
            methods = defaultdict(lambda: default_handler, http_methods.copy())
        else:
            methods = http_methods.copy()
        self.mappings.append((re.compile(path.decode('utf8')), methods, (path.find(r'\?')>-1) ))

    def __call__(self, environ, start_response):
        """
        Delegate request to the appropriate WSGI app.

        The following keys will be added to the WSGI's environ:

        wsgiorg.routing_args
            It's a tuple of a list and a dict. The structure is per this spec:
            http://www.wsgi.org/wsgi/Specifications/routing_args

        WSGIHandlerSelector.matched_request_methods
            It's a list of strings denoting other HTTP verbs / methods the
            matched URI (not chosen handler!) accepts for processing.
            This matters when

        """

        path = environ.get('GIT_PATH_INFO', '').decode('utf8')

        matches = None
        handler = None
        alternate_HTTP_verbs = set()
        query_string = (environ.get('QUERY_STRING') or '')

        # sanitizing the path:
        # turns garbage like this: r'//qwre/asdf/..*/*/*///.././../qwer/./..//../../.././//yuioghkj/../wrt.sdaf'
        # into something like this: /../../wrt.sdaf
        path = urlparse.urljoin(u'/', re.sub('//+','/',path.strip('/')))
        if not path.startswith('/../'): # meaning, if it's not a trash path
            for _regex, _registered_methods, _use_query_string in self.mappings:
                if _use_query_string:
                    matches = _regex.search(path + '?' + query_string)
                else:
                    matches = _regex.search(path)
                if matches:
                    # note, there is a chance that '_registered_methods' is an instance of
                    # collections.defaultdict, which means if default handler was
                    # defined it will be returned for all unmatched HTTP methods.
                    handler = _registered_methods[environ.get('REQUEST_METHOD','')]
                    if handler:
                        break
                    else:
                        alternate_HTTP_verbs.update(_registered_methods.keys())
        if handler:
            environ['GIT_PATH_INFO'] = path.encode('utf8')

            mg = list(environ.get('wsgiorg.routing_args') or ([],{}))
            mg[0] = list(mg[0]).append(matches.groups()),
            mg[1].update(matches.groupdict())
            environ['wsgiorg.routing_args'] = tuple(mg)

            return handler(environ, start_response)
        elif alternate_HTTP_verbs:
            # uugh... narrow miss. Regex matched some path, but the method was off.
            # let's advertize what methods we can do with this URI.
            return self.canned_handlers(
                environ,
                start_response,
                'method_not_allowed',
                headers = [('Allow', ', '.join(alternate_HTTP_verbs))]
                )
        else:
            return self.canned_handlers(environ, start_response, 'not_found')

class StaticWSGIServer(BaseWSGIClass):
    """
    Copyright (c) 2010  Daniel Dotsenko <dotsa@hotmail.com>
    Copyright (C) 2006 Luke Arno - http://lukearno.com/

    A simple WSGI-based static content server app.

    Relies on WSGIHandlerSelector for prepopulating some needed environ
    variables, cleaning up the URI, setting up default error handlers.
    """

    def __init__(self, **kw):
        '''
        Inputs:
            content_path (mandatory)
                String containing a file-system level path behaving as served root.

            bufsize (optional)
                File reader's buffer size. Defaults to 65536.

            gzip_response (optional) (must be named arg)
                Specify if we are to detect if gzip compression is supported
                by client and gzip the output. False by default.
        '''
        self.__dict__.update(kw)

    def __call__(self, environ, start_response):
        selector_matches = (environ.get('wsgiorg.routing_args') or ([],{}))[1]
        if 'working_path' in selector_matches:
            # working_path is a custom key that I just happened to decide to use
            # for marking the portion of the URI that is palatable for static serving.
            # 'working_path' is the name of a regex group fed to WSGIHandlerSelector
            path_info = selector_matches['working_path'].decode('utf8')
        else:
            path_info = environ.get('GIT_PATH_INFO', '').decode('utf8')

        # this, i hope, safely turns the relative path into OS-specific, absolute.
        full_path = os.path.abspath(os.path.join(self.content_path, path_info.strip('/')))
        _pp = os.path.abspath(self.content_path)

        if not full_path.startswith(_pp):
            return self.canned_handlers(environ, start_response, 'forbidden')
        if not os.path.isfile(full_path):
            return self.canned_handlers(environ, start_response, 'not_found')

        mtime = os.stat(full_path).st_mtime
        etag, last_modified =  str(mtime), email.utils.formatdate(mtime)
        headers = [
            ('Content-type', 'text/plain'),
            ('Date', email.utils.formatdate(time.time())),
            ('Last-Modified', last_modified),
            ('ETag', etag)
        ]
        headersIface = Headers(headers)
        headersIface['Content-Type'] = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'

        if_modified = environ.get('HTTP_IF_MODIFIED_SINCE')
        if if_modified and (email.utils.parsedate(if_modified) >= email.utils.parsedate(last_modified)):
            return self.canned_handlers(environ, start_response, 'not_modified', headers)
        if_none = environ.get('HTTP_IF_NONE_MATCH')
        if if_none and (if_none == '*' or etag in if_none):
            return self.canned_handlers(environ, start_response, 'not_modified', headers)

        file_like = open(full_path, 'rb')
        return self.package_response(file_like, environ, start_response, headers)

class GitHTTPBackendBase(BaseWSGIClass):
    git_folder_signature = set(['config', 'head', 'info', 'objects', 'refs'])
    repo_auto_create = True

    def has_access(self, **kw):
        '''
        User rights verification code.
        (This is NOT an authentication code. The authentication is handled by
        the server that hosts this WSGI app. We just go by the name of the
        already-authenticated user.
        '''
        return True

    def basic_checks(self, dataObj, environ, start_response):
        '''
        This function is shared by GitInfoRefs and SmartHTTPRPCHandler WSGI classes.
        It does the same basic steps - figure out working path, git command etc.

        dataObj - dictionary
        Because the dataObj passed in is mutable, it's a pointer. Once this function returns,
        this object, as created by calling class, will have the free-form updated data.

        Returns non-None object if an error was triggered (and already prepared in start_response).
        '''
        selector_matches = (environ.get('wsgiorg.routing_args') or ([],{}))[1]

        # making sure we have a compatible git command
        git_command = selector_matches.get('git_command') or ''
        if git_command not in ['git-upload-pack', 'git-receive-pack']: # TODO: this is bad for future compatibility. There may be more commands supported then.
            return self.canned_handlers(environ, start_response, 'bad_request')

        # TODO: Add "public" to "dynamic local" path conversion hook ups here.

        #############################################################
        # making sure local path is a valid git repo folder
        #
        repo_path = os.path.abspath(
            os.path.join(
                self.content_path,
                (selector_matches.get('working_path') or '').decode('utf8').strip('/').strip('\\')
                )
            )
        _pp = os.path.abspath(self.content_path)

        # this saves us from "hackers" putting relative paths after repo marker.
        if not repo_path.startswith(_pp):
            return self.canned_handlers(environ, start_response, 'forbidden')

        if not self.has_access(
            environ = environ,
            repo_path = repo_path,
            git_command = git_command
            ):
            return self.canned_handlers(environ, start_response, 'forbidden')

        try:
            files = os.listdir(repo_path)
        except:
            files = []
        if not self.git_folder_signature.issubset([i.lower() for i in files]):
            if not ( self.repo_auto_create and git_command == 'git-receive-pack' ):
                return self.canned_handlers(environ, start_response, 'not_found')
            else:
                # 1. traverse entire post-prefix path and check that each segment
                #    If it is ( a git folder OR a non-dir object ) forbid autocreate
                # 2. Create folderS
                # 3. Activate a bare git repo
                _pf = _pp
                _dirs = repo_path[len(_pp):].strip(os.sep).split(os.sep) or ['']
                for _dir in _dirs:
                    _pf = os.path.join(_pf,_dir)
                    if not os.path.exists(_pf):
                        try:
                            os.makedirs(repo_path)
                        except:
                            return self.canned_handlers(environ, start_response, 'not_found')
                        break
                    elif not os.path.isdir(_pf) or self.git_folder_signature.issubset([i.lower() for i in os.listdir(_pf)]):
                        return self.canned_handlers(environ, start_response, 'forbidden')
                if subprocess.call('git init --quiet --bare "%s"' % repo_path, shell=True):
                    return self.canned_handlers(environ, start_response, 'execution_failed')
        #
        #############################################################

        dataObj['git_command'] = git_command
        dataObj['repo_path'] = repo_path
        return None

class GitHTTPBackendInfoRefs(GitHTTPBackendBase):
    '''
    Implementation of a WSGI handler (app) specifically capable of responding
    to git-http-backend (Git Smart HTTP) /info/refs call over HTTP GET.

    This is the fist step in the RPC dialog. We have to reply with right content
    to show to Git client that we are an "intelligent" server.

    The "right" content is special header and custom top 2 rows of data in the response.
    '''
    def __init__(self, **kw):
        '''
        inputs:
            content_path (Mandatory) - Local file system path = root of served files.
            bufsize (Default = 65536) Chunk size for WSGI file feeding
            gzip_response (Default = False) Compress response body
        '''
        self.__dict__.update(kw)

    def __call__(self, environ, start_response):
        """WSGI Response producer for HTTP GET Git Smart HTTP /info/refs request."""

        dataObj = {}
        answer = self.basic_checks(dataObj, environ, start_response)
        if answer:
            # non-Null answer = there was an issue in basic_checks and it's time to return an HTTP error response
            return answer
        git_command = dataObj['git_command']
        repo_path = dataObj['repo_path']

        # note to self:
        # please, resist the urge to add '\n' to git capture and increment line count by 1.
        # The code in Git client not only does NOT need '\n', but actually blows up
        # if you sprinkle "flush" (0000) as "0001\n".
        # It reads binary, per number of bytes specified.
        # if you do add '\n' as part of data, count it.
        smart_server_advert = '# service=%s' % git_command

        try:
            out = subprocessio.SubprocessIOChunker(
                r'git %s --stateless-rpc --advertise-refs "%s"' % (git_command[4:], repo_path),
                starting_values = [ str(hex(len(smart_server_advert)+4)[2:].rjust(4,'0') + smart_server_advert + '0000') ],
                env = dict(CODE_REMOTE_USER=environ.get('REMOTE_USER', '')),
                )
        except (EnvironmentError) as e:
            environ['wsgi.errors'].write(str(e))
            return self.canned_handlers(environ, start_response, 'execution_failed')
#        except Exception as e:
#            environ['wsgi.errors'].write(str(e))
#            return self.canned_handlers(environ, start_response, 'internal_server_error')

        headers = [('Content-type','application/x-%s-advertisement' % str(git_command))]
        return self.package_response(
            out,
            environ,
            start_response,
            headers)

class GitHTTPBackendSmartHTTP(GitHTTPBackendBase):
    '''
    Implementation of a WSGI handler (app) specifically capable of responding
    to git-http-backend (Git Smart HTTP) RPC calls sent over HTTP POST.

    This is a layer that responds to HTTP POSTs to URIs like:
        /repo_folder_name/git-upload-pack?service=upload-pack (or same for receive-pack)

    This is a second step in the RPC dialog. Another handler for HTTP GETs to
    /repo_folder_name/info/refs (as implemented in a separate WSGI handler below)
    must reply in a specific way in order for the Git client to decide to talk here.
    '''
    def __init__(self, **kw):
        '''
        content_path
            Local file system path = root of served files.
        optional parameters may be passed as named arguments
            These include
                bufsize (Default = 65536) Chunk size for WSGI file feeding
                gzip_response (Default = False) Compress response body
        '''
        self.__dict__.update(kw)

    def __call__(self, environ, start_response):
        """
        WSGI Response producer for HTTP POST Git Smart HTTP requests.
        Reads commands and data from HTTP POST's body.
        returns an iterator obj with contents of git command's response to stdout
        """
        # 1. Determine git_command, repo_path
        # 2. Determine IN content (encoding)
        # 3. prepare OUT content (encoding, header)

        dataObj = {}
        answer = self.basic_checks(dataObj, environ, start_response)
        if answer:
            # this is a WSGI "trick". basic_checks have already prepared the headers,
            # and a response body (which is the 'answer') returned here.
            # presense of anything of truthiness in 'answer' = some ERROR have
            # already prepared a response and all I need to do is let go of the response.
            return answer

        git_command = dataObj['git_command']
        repo_path = dataObj['repo_path']

        try:
            _l = int(environ.get('CONTENT_LENGTH',''))
        except:
            _l = None

        # Note, depending on the WSGI server, the following handlings of chunked
        # request bodies are possible:
        # 1. This is WSGI 1.0-only compliant server. wsgi.input.read() is bottomless
        #    and Content-Length is absent.
        #    If WSGI app is assuming no size header = size header is Zero, app will respond with wrong data.
        #    (this code is not assuming None = zero data. We look deeper)
        #    If WSGI app is chunked-aware, but respects WSGI 1.0 only,
        #    it will reply with "501 Not Implemented"
        # 2. This is WSGI 1.0-compliant server that tries to accommodate Transfer-Encoding: chunked
        #    requests by caching the body and presenting it as wsgi.input file-like.
        #    Content-Length header is set to captured size and Transfer-Encoding
        #    header is removed. This is not per WSGI 1.0 spec, but is a good thing to do.
        #    All WSGI 1.x apps are happy.
        # 3. This is WSGI 1.1-compliant server that presents Transfer-Encoding: chunked
        #    requests as a file-like that yields an EOF at the end.
        #    Content-Length header is NOT set.
        #    Only WSGI 1.1 apps are happy. WSGI 1.0 apps are confused by lack of
        #    content-length header and blow up. (We are WSGI 1.1 app)

        # any WSGI server that claims to be HTTP/1.1 compliant must deal with chunked
        # If not #3 above, then #2 would be done by a self-respecting HTTP/1.1 server.

        wsgi_version = environ.get('wsgi.version',(1,0))
        if wsgi_version[0] >= 1 and wsgi_version[1] >= 1: # if it's 1.1 or higher.
            wsgi_input_has_EOF = True
        else:
            wsgi_input_has_EOF = False

        _i = environ.get('wsgi.input')
        if wsgi_input_has_EOF: # this is approximately equal "if server is WSGI 1.1 and above"
            stdin = _i
        else:
            if _l > self.bufsize: # too large to be a string in memory
                bs = self.bufsize
                btr = _l
                stdin = tempfile.TemporaryFile()
                while btr >= bs:
                    stdin.write(_i.read(bs))
                    btr -= bs
                stdin.write(_i.read(btr))
                stdin.flush()
                stdin.seek(0)
            else: # between zero and max memory buffer size = string or bytes
                stdin = _i.read(_l)

        cmd = r'git %s --stateless-rpc "%s"' % (git_command[4:], repo_path)
        _p = subprocess.Popen(cmd,
            bufsize = -1,
            shell = True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            env = dict(CODE_REMOTE_USER=environ.get('REMOTE_USER', '')),
            )
        if isinstance(stdin, file):
            out, _ = _p.communicate(stdin.read())
        else:
            try:
                fp = gzip.GzipFile(fileobj=StringIO(stdin))
                out, _ = _p.communicate(fp.read())
            except IOError:
                out, _ = _p.communicate(stdin)
        out = StringIO(out)

        if git_command == u'git-receive-pack':
            # updating refs manually after each push. Needed for pre-1.7.0.4 git clients using regular HTTP mode.
            subprocess.call(u'git --git-dir "%s" update-server-info' % repo_path, shell=True)

        headers = [('Content-type', 'application/x-%s-result' % git_command.encode('utf8'))]
        return self.package_response(
            out,
            environ,
            start_response,
            headers)

def assemble_WSGI_git_app(*args, **kw):
    '''
    Assembles basic WSGI-compatible application providing functionality of git-http-backend.

    content_path (Defaults to '.' = "current" directory)
        The path to the folder that will be the root of served files. Accepts relative paths.

    uri_marker (Defaults to '')
        Acts as a "virtual folder" separator between decorative URI portion and
        the actual (relative to content_path) path that will be appended to
        content_path and used for pulling an actual file.

        the URI does not have to start with contents of uri_marker. It can
        be preceeded by any number of "virtual" folders. For --uri_marker 'my'
        all of these will take you to the same repo:
            http://localhost/my/HEAD
            http://localhost/admysf/mylar/zxmy/my/HEAD
        This WSGI hanlder will cut and rebase the URI when it's time to read from file system.

        Default of '' means that no cutting marker is used, and whole URI after FQDN is
        used to find file relative to content_path.

    returns WSGI application instance.
    '''

    default_options = [
        ['content_path','.'],
        ['uri_marker','']
    ]
    args = list(args)
    options = dict(default_options)
    options.update(kw)
    while default_options and args:
        _d = default_options.pop(0)
        _a = args.pop(0)
        options[_d[0]] = _a
    options['content_path'] = os.path.abspath(options['content_path'].decode('utf8'))
    options['uri_marker'] = options['uri_marker'].decode('utf8')

    selector = WSGIHandlerSelector()
    generic_handler = StaticWSGIServer(**options)
    git_inforefs_handler = GitHTTPBackendInfoRefs(**options)
    git_rpc_handler = GitHTTPBackendSmartHTTP(**options)

    if options['uri_marker']:
        marker_regex = r'(?P<decorative_path>.*?)(?:/'+ options['uri_marker'] + ')'
    else:
        marker_regex = ''

    selector.add(
        marker_regex + r'(?P<working_path>.*?)/info/refs\?.*?service=(?P<git_command>git-[^&]+).*$',
        GET = git_inforefs_handler,
        HEAD = git_inforefs_handler
        )
    selector.add(
        marker_regex + r'(?P<working_path>.*)/(?P<git_command>git-[^/]+)$',
        POST = git_rpc_handler
        )
    selector.add(
        marker_regex + r'(?P<working_path>.*)$',
        GET = generic_handler,
        HEAD = generic_handler)

    return selector

#class ShowVarsWSGIApp(object):
#    def __init__(self, *args, **kw):
#        pass
#    def __call__(self, environ, start_response):
#        status = '200 OK'
#        response_headers = [('Content-type','text/plain')]
#        start_response(status, response_headers)
#        for key in sorted(environ.keys()):
#            yield '%s = %s\n' % (key, unicode(environ[key]).encode('utf8'))

if __name__ == "__main__":
    _help = r'''
git_http_backend.py - Python-based server supporting regular and "Smart HTTP"

Note only the folder that contains folders and object that you normally see
in .git folder is considered a "repo folder." This means that either a
"bare" folder name or a working folder's ".git" folder will be a "repo" folder
discussed in the examples below.

When "repo-auto-create on Push" is used, the server automatically creates "bare"
repo folders.

Note, the folder does NOT have to have ".git" in the name to be a "repo" folder.
You can name bare repo folders whatever you like. If the signature (right files
and folders are found inside) matches a typical git repo, it's a "repo."

Options:
--content_path (Defaults to '.' - current directory)
        Serving contents of folder path passed in. Accepts relative paths,
        including things like "./../" and resolves them agains current path.

        If you set this to actual .git folder, you don't need to specify the
        folder's name on URI.

--uri_marker (Defaults to '')
        Acts as a "virtual folder" - separator between decorative URI portion
        and the actual (relative to content_path) path that will be appended
        to content_path and used for pulling an actual file.

        the URI does not have to start with contents of uri_marker. It can
        be preceeded by any number of "virtual" folders.
        For --uri_marker 'my' all of these will take you to the same repo:
                http://localhost/my/HEAD
                http://localhost/admysf/mylar/zxmy/my/HEAD
        If you are using reverse proxy server, pick the virtual, decorative URI
        prefix / path of your choice. This hanlder will cut and rebase the URI.

        Default of '' means that no cutting marker is used, and whole URI after
        FQDN is used to find file relative to content_path.

--port (Defaults to 8080)

Examples:

cd c:\myproject_workingfolder\.git
c:\tools\git_http_backend\GitHttpBackend.py --port 80
        (Current path is used for serving.)
        This project's repo will be one and only served directly over
         http://localhost/

cd c:\repos_folder
c:\tools\git_http_backend\GitHttpBackend.py
        (note, no options are provided. Current path is used for serving.)
        If the c:\repos_folder contains repo1.git, repo2.git folders, they
        become available as:
         http://localhost:8080/repo1.git  and  http://localhost:8080/repo2.git

~/myscripts/GitHttpBackend.py --content_path "~/somepath/repofolder" --uri_marker "myrepo"
        Will serve chosen repo folder as http://localhost/myrepo/ or
        http://localhost:8080/does/not/matter/what/you/type/here/myrepo/
        This "repo uri marker" is useful for making a repo server appear as a
        part of some REST web application or make it appear as a part of server
        while serving it from behind a reverse proxy.

./GitHttpBackend.py --content_path ".." --port 80
        Will serve the folder above the "git_http_backend" (in which
        GitHttpBackend.py happened to be located.) A functional url could be
         http://localhost/git_http_backend/GitHttpBackend.py
        Let's assume the parent folder of git_http_backend folder has a ".git"
        folder. Then the repo could be accessed as:
         http://localhost/.git/
        This allows GitHttpBackend.py to be "self-serving" :)
'''
    import sys

    command_options = {
            'content_path' : '.',
            'uri_marker' : '',
            'port' : '8080'
        }
    lastKey = None
    for item in sys.argv:
        if item.startswith('--'):
            command_options[item[2:]] = True
            lastKey = item[2:]
        elif lastKey:
            command_options[lastKey] = item.strip('"').strip("'")
            lastKey = None

    content_path = os.path.abspath( command_options['content_path'] )

    if 'help' in command_options:
        print _help
    else:
        app = assemble_WSGI_git_app(
            content_path = content_path,
            uri_marker = command_options['uri_marker'],
            performance_settings = {
                'repo_auto_create':True
                }
        )

        # default Python's WSGI server. Replace with your choice of WSGI server
        #import cherrypy as wsgiserver
        from cherrypy import wsgiserver
        httpd = wsgiserver.CherryPyWSGIServer(('0.0.0.0',int(command_options['port'])),app)

        if command_options['uri_marker']:
            _s = '"/%s/".' % command_options['uri_marker']
            example_URI = '''http://localhost:%s/whatever/you/want/here/%s/myrepo.git
    (Note: "whatever/you/want/here" cannot include the "/%s/" segment)''' % (
            command_options['port'],
            command_options['uri_marker'],
            command_options['uri_marker'])
        else:
            _s = 'not chosen.'
            example_URI = 'http://localhost:%s/myrepo.git' % (command_options['port'])
        print '''
===========================================================================
Run this command with "--help" option to see available command-line options

Starting git-http-backend server...
        Port: %s
        Chosen repo folders' base file system path: %s
        URI segment indicating start of git repo foler name is %s

Example repo url would be:
    %s

Use Keyboard Interrupt key combination (usually CTRL+C) to stop the server
===========================================================================
''' % (command_options['port'], content_path, _s, example_URI)

        try:
            httpd.start()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.stop()
