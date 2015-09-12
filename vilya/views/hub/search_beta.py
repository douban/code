# -*- coding: utf-8 -*-

import json
from urllib import urlencode

from quixote.errors import TraversalError

from vilya.libs.template import st
from vilya.models.elastic.searcher import SearchEngine
from vilya.models.elastic import CodeSearch
from vilya.models.elastic.src_search import SrcSearch
from vilya.models.elastic.repo_search import RepoSearch
from vilya.models.elastic.user_search import UserSearch
from vilya.models.elastic.issue_pr_search import PullRequestSearch, IssueSearch
from vilya.models.elastic.consts import (
    SEARCH_URL_ROOT, ADMINS, K_REPO, K_CODE, K_USER, K_DOC, K_PULL, K_ISSUE,
    PERPAGE_LIMIT, SEARCH_KINDS, KIND_ORDERS_MAP, CODE_ORDERS)
from vilya.models.project import CodeDoubanProject
from vilya.views.util import require_login
from tasks import index_srcs_action, index_repos_action, index_users_action

KIND_CLASS_MAP = {
    K_REPO: RepoSearch,
    K_CODE: SrcSearch,
    K_DOC: CodeSearch,
    K_USER: UserSearch,
    K_PULL: PullRequestSearch,
    K_ISSUE: IssueSearch,
}


class SearchUI(object):

    _q_exports = ['count', 'xml']

    def __init__(self, project=None):
        self.project = project

    def _q_index(self, request):
        q = request.get_form_var('q', '')
        kind = request.get_form_var('kind', str(K_CODE))
        order = request.get_form_var('s', '')
        order = int(order) if order else ''
        page = request.get_form_var('page')
        page = int(page) if page and page.isdigit() else 1
        project = CodeDoubanProject.get_by_name(self.project) \
            if self.project else None
        state = request.get_form_var('state', '')
        language = request.get_form_var('language', '')
        doctype = request.get_form_var('doctype', '')

        if not kind.isdigit() and int(kind) not in SEARCH_KINDS:
            raise TraversalError()

        kind = int(kind)
        orders = KIND_ORDERS_MAP.get(kind, CODE_ORDERS)
        sort_data = orders.get(order)
        if sort_data:
            sort_data = sort_data[1]

        limit = PERPAGE_LIMIT
        total = 0
        offset = (page - 1) * limit
        result = {}
        formated_result = []
        facets = {}
        tdt = {}

        cls = KIND_CLASS_MAP.get(kind)

        by_project = by_language = by_state = by_doctype = False
        if project and kind in (K_DOC, K_CODE, K_PULL, K_ISSUE):
            by_project = True
        if language and kind == K_CODE:
            by_language = True
        if state and kind in (K_PULL, K_ISSUE):
            by_state = True
        if doctype and kind == K_DOC:
            by_doctype = True

        # for facets
        if kind in (K_CODE, K_PULL, K_ISSUE, K_DOC):
            project_id = project.id if by_project else None
            result = cls.search_a_phrase(
                phrase=q, from_=0, size=0, project_id=project_id)
            facets = cls.format_facets(result)
            for title, data in facets.iteritems():
                for item in data:
                    params = {'q': q, 'kind': kind, 's': order,
                              title: item['term']}
                    if by_project:
                        params.update(project_id=project_id)
                    item['url'] = '?' + urlencode(params)
                    # highlight current term
                    current = None
                    if by_language:
                        current = language
                    elif by_state:
                        current = state
                    elif by_doctype:
                        current = doctype
                    if current and current == item['term']:
                        item['selected'] = True
                        del params[title]
                        item['url'] = '?' + urlencode(params)

        # for search
        kwargs = dict(phrase=q, sort_data=sort_data, from_=offset, size=limit)
        if by_project:
            kwargs.update(project_id=project.id)
        if by_language:
            kwargs.update(language=language)
        if by_state:
            kwargs.update(state=state)
        if by_doctype:
            kwargs.update(doctype=doctype)

        result = cls.search_a_phrase(**kwargs)
        formated_result = cls.format_search_result(result)
        total = SearchEngine.get_count(result)
        pages = total / limit + 1 if total % limit > 0 else total / limit
        tdt.update(request=request, q=q, kind=kind, total=total, facets=facets,
                   language=language, state=state, doctype=doctype,
                   result=formated_result, orders=orders, s=order, page=page,
                   pages=pages)

        # for menu and pagenation
        SEARCH_URLS = dict()
        for k in SEARCH_KINDS:
            if project and k in (K_CODE, K_DOC, K_PULL, K_ISSUE):
                url_root = '/%s/search' % project.name
            else:
                url_root = SEARCH_URL_ROOT
            params = {'q': q, 'kind': k, 's': order}
            if state and k in (K_PULL, K_ISSUE):
                params.update({'state': state})
            if language and k == K_CODE:
                params.update({'language': language})
            if doctype and k == K_DOC:
                params.update({'doctype': doctype})
            url = '%s?' % url_root + urlencode(params)
            SEARCH_URLS[k] = url

        tdt.update(SEARCH_URLS=SEARCH_URLS)

        return st('search/base.html', **tdt)

    def count(self, request):
        request.response.set_content_type('application/json; charset=utf8')
        q = request.get_form_var('q', '')
        project = CodeDoubanProject.get_by_name(self.project) \
            if self.project else None
        state = request.get_form_var('state', '')
        language = request.get_form_var('language', '')
        doctype = request.get_form_var('doctype', '')
        counts = {}

        for kind, cls in KIND_CLASS_MAP.iteritems():
            kwargs = dict(phrase=q, from_=0, size=0)
            if project and kind in (K_DOC, K_CODE, K_PULL, K_ISSUE):
                kwargs.update(project_id=project.id)
            if language and kind == K_CODE:
                kwargs.update(language=language)
            if state and kind in (K_PULL, K_ISSUE):
                kwargs.update(state=state)
            if doctype and kind == K_DOC:
                kwargs.update(doctype=doctype)
            result = cls.search_a_phrase(**kwargs)
            counts[kind] = SearchEngine.get_count(result)

        tdt = {
            'q': q,
            'repos': counts[K_REPO],
            'codes': counts[K_CODE],
            'users': counts[K_USER],
            'docs': counts[K_DOC],
            'pulls': counts[K_PULL],
            'issues': counts[K_ISSUE],
        }
        return json.dumps(tdt)

    def _q_lookup(self, request, urlpart):
        if urlpart == 'repo_index':
            return RepoIndexUI()
        elif urlpart == 'user_index':
            return UserIndexUI()

    def xml(self, request):
        request.response.set_content_type(
            'application/opensearchdescription+xml')
        return st('search/firefox_search.xml')


class SrcIndexUI(object):
    _q_exports = []
    _actions = ['update', 'create', 'delete', 'update_mapping',
                'delete_mapping']

    def __init__(self, project_name):
        self.project = CodeDoubanProject.get_by_name(project_name)

    @require_login
    def _q_lookup(self, request, action):
        if (request.user.name in ADMINS
                and self.project and (action in self._actions)):
            index_srcs_action(action, self.project.id)
            return request.redirect(SEARCH_URL_ROOT + '?kind=%s' % K_CODE)
        raise TraversalError()


class RepoIndexUI(object):
    _q_exports = []
    _actions = ['update', 'create', 'delete', 'delete_mapping']

    @require_login
    def _q_lookup(self, request, action):
        if (request.user.name in ADMINS
                and (action in self._actions)):
            index_repos_action(action)
            return request.redirect(SEARCH_URL_ROOT + '?kind=%s' % K_REPO)
        raise TraversalError()


class UserIndexUI(object):
    _q_exports = []
    _actions = ['update', 'create', 'delete', 'delete_mapping']

    @require_login
    def _q_lookup(self, request, action):
        if (request.user.name in ADMINS
                and (action in self._actions)):
            index_users_action(action)
            return request.redirect(SEARCH_URL_ROOT + '?kind=%s' % K_USER)
