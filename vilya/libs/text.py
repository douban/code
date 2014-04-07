# -*- coding: utf-8 -*-

from __future__ import absolute_import
import urllib
import hashlib
from mikoto.libs.text import *
from mikoto.libs.emoji import *

from vilya.config import EMAIL_SUFFIX


def trunc_utf8(string, num, etc="..."):
    """truncate a utf-8 string, show as num chars.
    arg: string, a utf-8 encoding string; num, look like num chars
    return: a utf-8 string
    """
    try:
        gb = string.decode("utf8", "ignore")
    except UnicodeEncodeError:  # Already decoded
        gb = string
    gb = gb.encode("gb18030", "ignore")
    if num >= len(gb):
        return string
    if etc:
        etc_len = len(etc.decode("utf8", "ignore").encode("gb18030", "ignore"))
        trunc_idx = num - etc_len
    else:
        trunc_idx = num
    ret = gb[:trunc_idx].decode("gb18030", "ignore").encode("utf8")
    if etc:
        ret += etc
    return ret


EMAILRE = re.compile(
    r'^[_\.0-9a-zA-Z+-]+@([0-9a-zA-Z]+[0-9a-zA-Z-]*\.)+[a-zA-Z]{2,4}$')


def _validate_email(email):
    if not email:
        return False
    if len(email) >= 6:
        return EMAILRE.match(email) is not None
    return False


# FIXME: bad smell, useful ?
def email_normalizer(name, email):
    if _validate_email(email):
        return email
    else:
        return name + '@' + EMAIL_SUFFIX


def is_image(fname):
    return bool(RE_IMAGE_FILENAME.match(fname))


def is_binary(fname):
    ext = fname.split('.')
    if ext is None:
        return False
    if len(ext) == 1:
        return ext[0] not in SOURCE_FILE
    ext = '.' + ext[-1]
    if ext in IS_GENERATED:
        return False
    if ext in IGNORE_FILE_EXTS or ext not in (SOURCE_FILE + NOT_GENERATED):
        return True
    return False


def gravatar_url(email, size=140):
    default = "http://img3.douban.com/icon/user_normal.jpg"
    url = "http://douvatar.dapps.douban.com/mirror/" + hashlib.md5(
        email.encode('utf8').lower()).hexdigest() + "?"
    url += urllib.urlencode({'d': default, 's': str(size), 'r': 'x'})
    return url


def remove_unknown_character(text):
    if isinstance(text, str):
        return text.decode('utf-8', 'ignore').encode('utf-8', 'ignore')
    return text


def plural(count, single, plural):
    if count <= 1:
        return single
    else:
        return plural


def format_md_or_rst(path, src, project_name=None):
    src = decode_charset_to_unicode(src)
    if path.endswith('.md') or path.endswith('.markdown'):
        if project_name:
            return render_markdown_with_project(src, project_name=project_name)
        return render_markdown(src)

    if RST_RE.match(path):
        try:
            return docutils.core.publish_parts(src,
                                               writer_name='html')['html_body']
        except docutils.ApplicationError:
            pass

    lexer = TextLexer(encoding='utf-8')
    return highlight(src, lexer, HtmlFormatter(linenos=True,
                                               lineanchors='L',
                                               anchorlinenos=True,
                                               encoding='utf-8'))
