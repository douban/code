# -*- coding: utf-8 -*-

MCKEY_UPDATED_PROJECTS = "code:projects:updated"
MCKEY_CREATED_PROJECTS = "code:projects:created"
MCKEY_FORKED_PROJECTS = "code:projects:forked"
MCKEY_MOST_FORKED_PROJECTS = "code:projects:most_forked"

TEMP_BRANCH_MARKER = 'TEMPORARY_BRANCH'

#used only in dev environ, to mask the real git path with a specified path
DEFAULT_PATH = ''

PUBLIC_TIMELINE = 'public_timeline'
PROJECT_BC_KEY = '%s:%s'  # user:repo
COMMITS_MESSAGE_KEY = 'name:%s:ref:%s:path:%s'

PULL_REF_H = 'refs/pull/%s/head'
PULL_REF_M = 'refs/pull/%s/merge'
# BDB_PULL_BASE_KEY = 'pull_base:%s:%s' # deprecated

# no use
#COMMIT_COMMENT_TYPE = 'C'
#COMMIT_LINECOMMENT_TYPE = 'L'

COMMIT_COMMENT_UID_PATTERN = 'commit-comment-%s'
COMMIT_LINECOMMENT_UID_PATTERN = 'commit-linecomment-%s'

PULL_COMMENT_UID_PATTERN = 'comment-%s'
PULL_CODEREVIEW_UID_PATTERN = 'review-%s'
PULL_EMAIL_IN_REPLY_TO = '<%s-pull-%s@code>'

ISSUE_COMMENT_UID_PATTERN = 'comment-%s'

TEAM_ADD_MEMBER_UID_PATTERN = 'team-add-member-%s'

NEW_PULL_EMAIL_TITLE = '[%s] %s (#%s)'  # [project name] pull request title (#ticket id)
NEW_PULL_EMAIL_BODY = \
    """%s
<br><br>—<br>
<a href="%s">View it on Code</a>.<img src='%s' height='1' width='1'>"""

RE_PULL_EMAIL_TITLE = 'Re: [%s] %s (#%s)'  # [project name] pull request title (#ticket id)
RE_PULL_EMAIL_BODY = NEW_PULL_EMAIL_BODY

NEW_ISSUE_EMAIL_TITLE = '[%s] %s (#%s)'  # [project name] issue title (#issue id)
RE_ISSUE_EMAIL_TITLE = 'Re: [%s] %s (#%s)'  # [project name] issue title (#issue id)
ISSUE_COMMENT_EMAIL_TITLE = 'Re: [%s] %s (#%s)'  # [project name] issue title (#issue id)
ISSUE_EMAIL_BODY = ISSUE_COMMENT_EMAIL_BODY = NEW_PULL_EMAIL_BODY


ISSUE_EMAIL_IN_REPLY_TO = '<%s-issue-%s@code>'

PEOPLE_PROJECT = '0'
ORGANIZATION_PROJECT = '1'
MIRROR_PROJECT = '2'

TEAM_OWNER = 1
TEAM_MEMBER = 2

TEAM_IDENTITY_INFO = {
    TEAM_MEMBER: {
        "show_name": "member",
        "name": "member",
    },
    TEAM_OWNER: {
        "show_name": "owner",
        "name": "owner",
    },
}

# line comment
LINECOMMENT_INDEX_EMPTY = -1
LINECOMMENT_INDEX_INVALID = -2  # 用于没有 linenum 的旧数据

LINECOMMENT_TYPE_COMMIT = 1
LINECOMMENT_TYPE_PULL = 2

PATCH_TYPE = {
    "A": "added",
    "D": "removed",
    "M": "modified",
    "R": "renamed",
}

MOBILE_MAIN_PATH = {
    "/": "Homepage",
    "/hub/my_pull_requests/": "My PullRequests",
    "/hub/my_issues/": "My Issues",
}

MY_PULL_REQUESTS_TAB_INFO = [
    {"url": "/hub/my_pull_requests/", "type": "invited", "text": "Invited"},
    {"url": "/hub/my_pull_requests/?list_type=participated", "type": "participated", "text": "Participated"},
    {"url": "/hub/my_pull_requests/?list_type=yours", "type": "your", "text": "Yours"},
    {"url": "/hub/my_pull_requests/?list_type=explore", "type": "explore", "text": "Explore"}
]

## remove this
NOTIFY_ON = u'1'
NOTIFY_OFF = u'0'

SETTING_ENABLE = u'1'
SETTING_DISABLE = u'0'

# font settings
FONTS = {
    'default': 'source',
    'fonts': {
        'source': 'Source Code Pro',
        'consolas': 'Consolas',
        'monaco': 'Monaco',
        'courier': 'Courier',
        'dejavu': 'DejaVu Sans Mono',
        'ubuntu': 'Ubuntu Mono',
    }
}

MIRROR_STATE_CLONED = 1
MIRROR_STATE_CLONING = 0
MIRROR_WITH_PROXY = 1
MIRROR_NOT_PROXY = 0
MIRROR_HTTP_PROXY = "http://vpn2:8118"

# used in table `ticket_nodes`
TICKET_NODE_TYPE_OPEN = 1
TICKET_NODE_TYPE_CLOSE = 2
TICKET_NODE_TYPE_MERGE = 3
TICKET_NODE_TYPE_COMMIT = 4
TICKET_NODE_TYPE_COMMENT = 5
TICKET_NODE_TYPE_CODEREVIEW = 6  # deprecated
TICKET_NODE_TYPE_LINECOMMENT = 7

API_BASE = "http://code.dapps.douban.com/api"

API_ENDPOINTS = {
    "current_user_url": "%s%s" % (API_BASE, "/user/"),
    "following_url": "%s%s" % (API_BASE, "/user/following/{target_user}"),
    "user_url": "%s%s" % (API_BASE, "/users/{user}"),
    "team_url": "%s%s" % (API_BASE, "/teams/{team}"),
    "gist_url": "%s%s" % (API_BASE, "/gists/{gist_id}"),
}

DOUBAN_EMAIL = (
    '@douban.com',
    '@intern.douban.com',
)

MIRROR_EMAIL = 'mirror@douban.com'

# used in table `users`
USER_ROLE_DEFAULT= 0
USER_ROLE_STAFF = 1
USER_ROLE_INTERN = 2

# sphinx
DOC_EXT = '.sphinx_docs'
SPHINX_BUILD_DOCTREES = '.build/doctrees'
SPHINX_BUILDER_TYPES = ['html', 'pickle', 'raw']
SPHINX_STATIC_PATHS = ['_images', '_sources', '_static']
SPHINX_DEFAULT_CHECKOUT_ROOT = False

# kind of code object
K_PULL = 1001
K_ISSUE = 1002

# tags color
TAG_COLORS = {
    'e11d21': 'fff',
    'eb6420': 'fff',
    'fbca04': '332900',
    '009800': 'fff',
    '006b75': 'fff',
    '207de5': 'fff',
    '0052cc': 'fff',
    '5319e7': 'fff',
    'f7c6c7': '332829',
    'fad8c7': '332c28',
    'fef2c0': '333026',
    'bfe5bf': '2a332a',
    'c7def8': '282d33',
    'bfdadc': '2c3233',
    'bfd4f2': '282c33',
    'd4c5f9': '2b2833',
    'cccccc': '333333',
    '84b6eb': '1c2733',
    'e6e6e6': '333333',
    'ffffff': '333333',
    'cc317c': 'fff',
}

PERM_PULL = 1
PERM_MERGE = 10
PERM_PUSH = 100
PERM_ADMIN = 1000

PERM_TEXT = {
    PERM_PULL: 'pull',
    PERM_MERGE: 'merge',
    PERM_PUSH: 'push',
    PERM_ADMIN: 'admin',
}

TELCHAR_URL = 'http://telchar.dapps.douban.com'
FEATURE_HOOK_URLS = frozenset([
    TELCHAR_URL
])

UPLOAD_URL = 'http://p.dapps.douban.com'
