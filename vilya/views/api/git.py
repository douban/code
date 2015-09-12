# coding: UTF-8

from __future__ import absolute_import
import json
import PyRSS2Gen as RSS2

from vilya.config import DOMAIN
from vilya.libs.reltime import compute_relative_time
from vilya.views.api.utils import jsonize


class GitUI(object):
    _q_exports = ['branches', 'allfiles', 'lastlog', 'lineblame']

    def __init__(self, project):
        self.project = project

    @jsonize
    def branches(self, request):
        return self.project.repo.branches

    @jsonize
    def allfiles(self, request):
        branch = request.get_form_var('branch', 'HEAD')
        repo = self.project.repo
        # FIXME: path sort order in ellen
        tree = repo.get_tree(branch, recursive=True)
        return [f['path'] for f in tree]

    @jsonize
    def lastlog(self, request):
        path = request.get_form_var('path')
        repo = self.project.repo
        commit = repo.get_last_commit('HEAD', path=path)
        data = {"author": '',
                "age": '',
                "parents": [],
                "date": '',
                "commit": '',
                "message": '',
                "email": ''}
        if commit:
            data = commit.as_dict()
            data['commit'] = data['id']
            data['age'] = compute_relative_time(commit.author_timestamp)
        return data

    @jsonize
    def lineblame(self, request):
        rev = request.get_form_var('rev', 'HEAD')
        path = request.get_form_var('path')
        lineno = request.get_form_var('lineno', 1)
        dumb = {
            'author': '',
            'time': '',
            'summary': '',
            'sha': '',
        }
        if not path:
            return dumb
        blame = self.project.repo.blame_file(rev, path, lineno=int(lineno))
        for hunk in blame.hunks:
            for line in hunk.lines:
                if line.no == int(lineno):
                    dumb['author'] = line.commit.author.name
                    dumb['time'] = line.commit.author_time
                    dumb['summary'] = line.commit.message_header
                    dumb['sha'] = line.commit.sha
        return dumb


class CommitsUI(object):

    _q_exports = []

    def __init__(self, request, project):
        self.project = project

    def __call__(self, request):
        return self._index(request)

    def _q_index(self, request):
        return self._index(request)

    def _gen_rss(self, data):
        proj_name = self.project.name
        items = []
        for d in data:
            items.append(RSS2.RSSItem(
                title=d.get('message', ''),
                link="%s/%s/commit/%s" % (
                    DOMAIN, proj_name, d.get('id', '')),
                author=d.get('email', ''),
                pubDate=d.get('date', ''),
            ))
        rss = RSS2.RSS2(
            title="%s RSS Feed" % proj_name,
            link="%s/api/%s/commits" % (DOMAIN, proj_name),
            description="%s RSS Feed" % proj_name,
            items=items,
        )
        return rss.to_xml('utf-8')

    def _index(self, request):
        begin = request.get_form_var('begin') or 'HEAD~5'
        end = request.get_form_var('end') or 'HEAD'
        format = request.get_form_var('format') or 'json'
        repo = self.project.repo
        data = []
        if repo:
            commits = repo.get_commits(end,
                                       from_ref=begin)
            data = [commit.as_dict(with_files=True) for commit in commits]

        if format == 'rss':
            return self._gen_rss(data)
        else:
            return json.dumps(data)

    def _q_lookup(self, request, sha):
        data = {}
        repo = self.project.repo
        commit = repo.get_commit(sha)
        if commit:
            data = commit.as_dict(with_files=True)
        return json.dumps(data)
