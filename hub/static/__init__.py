#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''静态文件支持

mako中得到静态文件的url：
<%!
from static import static
%>
${static('/js/douban.js')}

mako中嵌入css、js等内容：
<%!
from static import istatic
%>
<script>
${istatic('/js/sns/tribe/manage_members.js')|n}
</script>
'''

from copy import copy
from os.path import join, exists, normpath, dirname
import re
import functools

from quixote.errors import TraversalError

from vilya.config import CODE_DIR

__all__ = ['static', 'istatic', 'get_static', 'get_static_content',
           'get_file_content', 'CyclicImportStaticException']


STATIC_FILE_DIR = '../dist'
BUILTIN_FILE_DIR = '../hub/static'

CSS_URL_IMPORT_REGEX = re.compile(r'url\(\'(.*)\'\)')


def css_js_url(path):
    return path


class StaticManager(object):
    '''维护静态文件版本信息'''
    static_type = 'css'
    file_types = []

    def __init__(self, static_site=''):
        self.static_site = static_site
        self.static_dir = join(
            CODE_DIR, STATIC_FILE_DIR, self.static_type)

    def get_packaged_filename(self, filename):
        '''打包之后应该存储的文件名'''
        return join(self.static_dir, filename)

    def static(self, path, compressed=False, convert_url_func=None):
        from vilya.libs.template import request as req

        '''获取静态文件的访问url'''
        filename = path[len(self.static_type) + 2:]  # 去掉前缀的 /css/
        file_path = join(self.static_dir, filename)

        if exists(file_path):

            if compressed and self.static_type == 'js':
                from dae.api import cdn
                cdn_fn_name = 'js_url' if self.static_type == 'js' else 'css_url'
                cdn_fn = getattr(cdn, cdn_fn_name)
                file_path = join(STATIC_FILE_DIR, self.static_type, filename)
                url = cdn_fn(file_path)
            else:
                # 如果文件的确存在，说明是本地新增文件，直接返回本地开发的地址
                url = path

        else:
            raise AttributeError('static file %s not exists.' % path)

        set_content_type(req, file_path)

        if convert_url_func:
            url = convert_url_func(url)

        if self.static_site and not url.startswith('http'):
            url = self.static_site + url

        if req and req.get_scheme() == 'https':
            url = re.sub(r'http://', 'https://', url)
            return re.sub(r'https://img\d+', 'https://img0', url)

        return url


class CSSStaticManager(StaticManager):
    '''所有css文件信息'''
    static_type = 'css'
    file_types = ['css']


class JSStaticManager(StaticManager):
    '''所有js文件信息'''
    static_type = 'js'
    file_types = ['js']


def check_static_path(path):
    '''检查静态文件名，如果不符合规范，则抛出异常'''
    def file_ends_with_digit(path, extension):
        '''除去后缀名，文件名是否以数字结尾。

        数字结尾用来区分文件的版本，如果原始文件名以数字结尾，会造成无法访问'''
        filename = path[:-len(extension)]
        return filename and filename[-1].isdigit()

    if path.startswith('/css/'):
        if file_ends_with_digit(path, '.css'):
            raise Exception('static filename ends with digit: %r' % (path))
    elif path.startswith('/js/'):
        if file_ends_with_digit(path, '.js'):
            raise Exception('static filename ends with digit: %r' % (path))


__CSS_MANAGER = None
__JS_MANAGER = None


def get_static_manager(static_path):
    '''获取单例化的管理器'''
    from vilya.config import DOMAIN

    global __CSS_MANAGER
    global __JS_MANAGER
    if not __CSS_MANAGER:
        __CSS_MANAGER = CSSStaticManager(static_site=DOMAIN)
    if not __JS_MANAGER:
        __JS_MANAGER = JSStaticManager(static_site=DOMAIN)

    if static_path.startswith('/js/'):
        return __JS_MANAGER
    else:
        return __CSS_MANAGER


def static(static_file_path):
    '''获取静态文件访问的url

    mako中得到静态文件的url：
    <%!
    from static import static
    %>
    ${static('/js/douban.js')}
    '''
    if not static_file_path.startswith('/'):
        raise Exception('static file path should starts with / but %r' %
                        static_file_path)

    """
    from vilya.libs.template import request
    if hasattr(request, "is_mobile") and request.is_mobile:
        mobile_uri = get_mobile_uri(static_file_path)
        try:
            url = _static_helper(mobile_uri)
            if url: return url
        except (IOError, AttributeError):
            pass
    """
    # 厂外不能使用static自动生成cdn地址. 直接转化下
    # '/css/a.css' -> '/static/css/a.css'
    # return _static_helper(static_file_path)
    return '/static' + static_file_path


def _static_helper(static_file_path):
    from config import CSS_JS_DEVELOP_MODE
    from vilya.libs.template import request as req

    # 简单的单例模式(singlton)，避免扫描文件等做重复计算，提交执行效率

    url = ''
    path = str(static_file_path)
    check_static_path(path)
    if path.startswith('/css/') or path.startswith('/js/'):
        url = get_static_manager(path).static(path,
                                              compressed=not CSS_JS_DEVELOP_MODE,
                                              convert_url_func=css_js_url)
    else:
        raise AttributeError('can not handle static file %r' % path)

    # 反劫持。如果发现有hj=tqs的cookie，就给url后增加?tqs=<date>
    if req and hasattr(req, 'get_cookie') and req.get_cookie('hj') == 'tqs':
        url = '%s?tqs=20110616' % url
        # 反劫持。img3 CDN被劫持
        if 'img3.douban.com' in url and static_file_path.startswith('/js/'):
            url = url.replace('img3.douban.com', 'img4.douban.com')

    return url


def set_content_type(request, path):
    if path.endswith('.js'):
        request.response.set_content_type('application/x-javascript')
    elif path.endswith('.css'):
        request.response.set_content_type('text/css')
    elif path.endswith('.svg'):
        request.response.set_content_type('image/svg+xml')


def get_file_content(path):
    '''获取静态文件的原始内容'''
    if not path.startswith('/'):
        raise Exception('static file path should starts with / but %r' %
                        path)
    if not path.startswith('/' + STATIC_FILE_DIR):
        file_path = '%s/%s%s' % (CODE_DIR, STATIC_FILE_DIR, path)
    else:
        file_path = '%s%s' % (CODE_DIR, path)
    try:
        return open(file_path).read()
    except IOError:
        file_path = '%s/%s%s' % (CODE_DIR, BUILTIN_FILE_DIR, path)
        try:
            return open(file_path).read()
        except IOError:
            raise TraversalError('static file not exists')


class ModuleStatic(object):
    '''模块化静态文件实例

    只用于模块化处理过程的计算。'''

    def __init__(self, static_path, converters, final_converter=None,
                 debug=False):

        self.path = static_path.strip('";')
        self.converters = converters or []
        self.final_converter = final_converter
        self.debug = debug
        self.imported_files = set()

        self.content = get_file_content(self.path)

        if not self.content.endswith('\n'):
            self.content += '\n'
        self.dependence = None

    def static_content_convert(self):
        '''对模块化的静态文件内容做处理、转化'''
        for converter in self.converters:
            converter(self)

    def clone(self, static_path):
        '''克隆实例，并记录实例在处理过程中的上下级关系'''
        try:
            clone = ModuleStatic(static_path, converters=self.converters,
                                 debug=self.debug)
        except IOError:
            raise Exception('read static file %s failed caused by %s' % (
                static_path, self.path))
        clone.dependence = self
        clone.imported_files = copy(self.imported_files)
        return clone

    def is_depended(self, path):
        '''指定文件是否存在于依赖链中'''
        parent = self.dependence
        while parent:
            if path == parent.path:
                return True
            parent = parent.dependence
        return False

    def is_imported(self, path):
        '''指定文件是否已经被导入过'''
        node = self
        while node:
            if path in node.imported_files:
                return True
            node = node.dependence
        return False

    def imported(self, mod):
        '''记录指定文件已经被导入过'''
        self.imported_files |= set([mod.path])
        self.imported_files |= mod.imported_files

    @property
    def final(self):
        '''获取静态文件的最终内容'''
        self.static_content_convert()
        if self.final_converter:
            self.final_converter(self)
        return self.content


class CyclicImportStaticException(Exception):
    '''静态文件循环导入错误'''

    def __init__(self, static_file, cyclic_imported_file):
        Exception.__init__(self)
        self.static_file = static_file
        self.cyclic_imported_file = cyclic_imported_file

    def __str__(self):
        return 'cyclic import %r in static file %r' % (self.static_file,
                                                       self.cyclic_imported_file)

RE_IMPORT = re.compile(r'(?m)'
                       r'(?#single line)^[ \t]*@import (\s*[^\s]+\s*)$'
                       r'|(?#cpp style comment)^//[ \t]*@import (\s*[^\s]+\s*)$'
                       r'|(?#c style comment)^/\*[ \t]*@import (\s*[^\s]+)\s*\*/\s*$'
                       )


def import_converter(module, file_type):
    '''解析模块化语法 @import /js/name.js，并嵌入对应文件的内容'''
    def get_content(match):
        '''发现@import语法，导入相关文件'''
        (single_line, cpp_style, c_style) = match.groups()
        path = single_line or cpp_style or c_style
        path = path.strip().strip(';"')

        if '.' not in path.rsplit('/', 1)[-1]:
            path = '%s.%s' % (path, file_type)

        match = CSS_URL_IMPORT_REGEX.search(path)
        if match:
            path = match.groups()[0]
            path = join(dirname(module.path), path)

        if not path[0] in './':
            raise Exception(
                "import path should start with . or / %s imported in %s" % (path, module.path))

        if path[0] != '/':
            path = normpath(join(module.path.rsplit('/', 1)[0], path))

        clone = module.clone(path)

        if module.path == path:
            # 导入自己
            raise CyclicImportStaticException(path, path)
        if module.is_depended(path):
            # 循环导入
            raise CyclicImportStaticException(module.path, path)
        if module.is_imported(path):
            # 被依赖多次，且已经被导入过，就不需再次导入
            if module.debug:
                return '/* SKIP IMPORTED @import %s */\n' % path
            return ''

        content = clone.final
        module.imported(clone)

        content = content.rstrip()
        if module.debug:
            content = '/* BEGIN @import %s */\n%s\n/* END @import %s */' % (
                path, content, path)
        content += '\n'

        return content

    content = RE_IMPORT.sub(get_content, module.content)
    module.content = content

JS_CONVERTERS = [functools.partial(import_converter, file_type='js')]
CSS_CONVERTERS = [functools.partial(import_converter, file_type='css')]


def get_static_content(static_path, converters=None, debug=False):
    '''获取静态文件，支持模块化等特性'''

    if not static_path.startswith('/'):
        raise Exception('static file path should starts with / but %r' %
                        static_path)

    if converters is None:
        if static_path.endswith('.js'):
            converters = JS_CONVERTERS
        else:
            converters = CSS_CONVERTERS
            # final_converter = scss_converter
        final_converter = None
    return ModuleStatic(static_path, debug=debug, converters=converters,
                        final_converter=final_converter).final


def get_static(static_path):
    '''获取静态文件内容，支持模块化 @import 语法

    使用方法：
    from static import get_static
    js_content = get_static('/js/douban.js')
    '''
    try:
        from vilya.config import CSS_JS_DEVELOP_MODE
        debug = CSS_JS_DEVELOP_MODE
    except ImportError:
        # 自动打包程序的执行环境中没有 luzong 代码
        debug = False
    return get_static_content(static_path, debug=debug)


def get_packaged_static(static_path):
    '''获取压缩过的静态文件内容。

    线上环境使用'''
    manager = get_static_manager(static_path)
    packaged = manager.get_packaged_filename(static_path)
    return get_file_content(packaged)


def format_javascript_variable(name, obj):
    '''格式化js格式的var定义，并对字符串进行转义'''
    value = str(obj)
    if not isinstance(obj, (int, float)):
        value = "'%s'" % value.replace("'", r"\'")
    return 'var %s=%s;\n' % (name, value)


CSS_URL_REG = re.compile(r'''(?<!_)url\((?:'|")?(/.*?)(?:'|")?\)''')


def add_static_host(content):

    def replace_helper(matchobj):
        url = matchobj.group(1)
        return '''url(%s)''' % (css_js_url(url))

    return re.sub(CSS_URL_REG, replace_helper, content)


def istatic(static_path, **kwargs):
    '''把静态文件内容内嵌(inline)入html模板中

    输出内容中不包含script标签。
    '''
    """
    if getattr(request, 'is_mobile', None):
        mobile_uri = get_mobile_uri(static_path)
        try:
            content = _istatic_helper(mobile_uri)
            if content: return content
        except (IOError, AttributeError):
            pass
    """
    return _istatic_helper(static_path, **kwargs)


def _istatic_helper(static_path, **kwargs):
    try:
        from config import CSS_JS_DEVELOP_MODE
        online = not CSS_JS_DEVELOP_MODE
    except ImportError:
        # 自动打包程序的执行环境中没有 luzong 代码
        online = False

    if not static_path.startswith('/'):
        raise Exception('static file path should starts with / but %r' %
                        static_path)

    check_static_path(static_path)
    if online:
        content = get_packaged_static(static_path)
    else:
        content = get_static(static_path)

    if static_path.endswith('css'):
        content = add_static_host(content)

    if kwargs:
        prepend_content = ''.join(format_javascript_variable(*item)
                                  for item in sorted(kwargs.items()))
        return prepend_content + content
    else:
        return content
