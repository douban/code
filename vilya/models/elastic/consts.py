# -*- coding: utf-8 -*-

SEARCH_URL_ROOT = '/hub/search_beta'

ADMINS = ['qingfeng', 'xutao', 'xyb', 'huanghuang', 'liwentao', 'fanjianjin',
          'testuser']

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

SRC_SIZE_LIMIT = 500000

PERPAGE_LIMIT = 10

WATCHS = 1
FORKS = 2
UPDATED = 3
INDEXED = 4
BADGES = 5
PRAISES = 6
FOLLOWERS = 7
REPOS = 8
CREATED = 9

SEARCH_KINDS = (
    K_REPO,
    K_CODE,
    K_USER,
    K_DOC,
    K_PULL,
    K_ISSUE,
) = range(6)

SEARCH_KIND_NAMES = (
    'Repositories',
    'Codes',
    'Users',
    'Docs',
    'Pulls',
    'Issues',
)

SEARCH_KIND_ICON_NAMES = (
    'mini-icon-public-repo',
    'mini-icon-code',
    'mini-icon-person',
    'mini-icon-doc',
    'mini-icon-pull',
    'mini-icon-issue',
)

REPO_ORDERS = {
    WATCHS: ('Watchs', [{'watched_count': 'desc'}, '_score']),
    FORKS: ('Forks', [{'forked_count': 'desc'}, '_score']),
    UPDATED: ('Updated', [{'last_updated': 'desc'}, '_score']),
}

USER_ORDERS = {
    BADGES: ('Badges', [{'badges_count': 'desc'}, '_score']),
    PRAISES: ('Praises', [{'praises_count': 'desc'}, '_score']),
    FOLLOWERS: ('Followers', [{'followers_count': 'desc'}, '_score']),
    REPOS: ('Repositories', [{'repos_count': 'desc'}, '_score']),
}

CODE_ORDERS = {
    UPDATED: ('Updated', [{'last_updated': 'desc'}, '_score']),
    CREATED: ('Created', [{'commit_time': 'desc'}, '_score']),
}

PULL_ORDERS = {
    UPDATED: ('Updated', [{'base.repo.pushed_at': 'desc'}, '_score']),
    CREATED: ('Created', [{'created_at': 'desc'}, '_score']),
}

ISSUE_ORDERS = {
    UPDATED: ('Updated', [{'updated_at': 'desc'}, '_score']),
    CREATED: ('Created', [{'created_at': 'desc'}, '_score']),
}

DOC_ORDERS = {
    CREATED: ('Created', [{'time': 'desc'}, '_score']),
}

KIND_ORDERS_MAP = {
    K_REPO: REPO_ORDERS,
    K_USER: USER_ORDERS,
    K_DOC: DOC_ORDERS,
    K_CODE: CODE_ORDERS,
    K_ISSUE: ISSUE_ORDERS,
    K_PULL: PULL_ORDERS,
}
