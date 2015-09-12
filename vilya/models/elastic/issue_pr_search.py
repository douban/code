# -*- coding: utf-8 -*-

import logging

from vilya.libs.store import store
from vilya.libs.text import trunc_utf8

from vilya.models.project_issue import ProjectIssue
from vilya.models.pull import PullRequest
from vilya.models.ticket import Ticket
from vilya.models.project import CodeDoubanProject
from vilya.models.user import User
from vilya.models.elastic.indexer import IndexEngine
from vilya.models.elastic.searcher import SearchEngine


class IssuePRSearch(object):
    type_name = ''

    @classmethod
    def index_an_object(cls, serial, data):
        return IndexEngine.create_a_index(cls.type_name, serial, data)

    @classmethod
    def search_a_phrase(cls, phrase, project_id=None, from_=0, size=20,
                        state=None, sort_data=None):
        filter_list = []
        if project_id:
            if cls.type_name == "issue":
                key = "project_id"
            else:
                key = "to_proj_id"
            filter_list.append({
                "term": {
                    key: project_id
                }
            })
        if state:
            filter_list.append({"term": {"state": state}})
        if filter_list:
            filter_data = {"and": filter_list}
        else:
            filter_data = None

        highlight_data = {
            "fields": {
                "description": {"number_of_fragments": 0}
            }
        }

        facets_data = {
            "state": {
                "terms": {
                    "field": "state"
                }
            }
        }

        result = SearchEngine.search_a_phrase(cls.type_name, phrase, from_,
                                              size, sort_data=sort_data,
                                              filter_data=filter_data,
                                              highlight_data=highlight_data,
                                              facets_data=facets_data)
        return result

    @classmethod
    def index_a_project(cls, project):
        IssueSearch.index_a_project_issue(project)
        PullRequestSearch.index_a_project_pr(project)

    @classmethod
    def format_facets(cls, result):
        if not SearchEngine.check_result(result):
            return {}
        formatted = dict(state=result['facets']['state']['terms'])
        return formatted


class IssueSearch(IssuePRSearch):

    type_name = "issue"

    @classmethod
    def index_a_project_issue(cls, project):
        issues = ProjectIssue._get_issues_by_project_id(project.id)
        for issue in issues:
            data = issue.as_dict()
            if data:
                serial = "%s_%s" % (project.index_name, issue.number)
                cls.index_an_object(serial, data)

    @classmethod
    def format_search_result(cls, result):
        if not SearchEngine.check_result(result):
            return []
        formatted = []
        result = result['hits']['hits']
        for r in result:
            _source = r['_source']
            try:
                hl_description = r['highlight']['description'][0]
            except:
                logging.debug('No highlight for %s', _source)
                hl_description = ''
            description = _source.get('description')
            sr = dict(
                issue_id=_source.get('issue_id'),
                description=description if description else '',
                hl_description=hl_description,
            )
            if not sr['issue_id']:
                logging.warn('Invaild issue search result, skip: %s', _source)
                continue
            sr = IssueResult(**sr)
            formatted.append(sr)
        return formatted


class PullRequestSearch(IssuePRSearch):

    type_name = "pull"

    @classmethod
    def index_a_project_pr(cls, project):
        rs = store.execute("select ticket_id from pullreq "
                           "where to_project=%s", project.id)
        for r, in rs:
            pr = PullRequest.get_by_proj_and_ticket(project.id, r)
            if pr:
                data = pr.as_dict()
                if data:
                    serial = "%s_%s" % (project.index_name, r)
                    cls.index_an_object(serial, data)

    @classmethod
    def format_search_result(cls, result):
        if not SearchEngine.check_result(result):
            return []
        formatted = []
        result = result['hits']['hits']
        for r in result:
            _source = r['_source']
            try:
                hl_description = r['highlight']['description'][0]
            except:
                logging.debug('No highlight for %s', _source)
                hl_description = ''
            sr = dict(
                ticket_number=_source.get('ticket_id'),
                project_id=_source.get('to_proj_id'),
                hl_description=hl_description,
            )
            if not sr['project_id'] or not sr['ticket_number']:
                logging.warn(
                    'Invaild pullrequest search result, skip: %s', _source)
                continue
            sr = PullResult(**sr)
            formatted.append(sr)
        return formatted


class PullResult(object):

    def __init__(self, project_id, ticket_number, hl_description):
        self.ticket = Ticket.get_by_projectid_and_ticketnumber(
            project_id, ticket_number)
        self.ticket_project = CodeDoubanProject.get(self.ticket.project_id)
        self.author = User(self.ticket.author)
        self.ticket_url = self.ticket.url
        self.hl_description = hl_description if hl_description \
            else self.ticket.description

    def snippet(self):
        desc = self.hl_description
        return trunc_utf8(desc, 300)


class IssueResult(object):

    def __init__(self, issue_id, description, hl_description):
        self.issue = ProjectIssue.get_by_issue_id(issue_id) \
            if issue_id else None
        if self.issue and self.issue.description:
            description = self.issue.description
        self.description = description
        self.hl_description = hl_description or description

    def snippet(self):
        desc = self.hl_description
        return trunc_utf8(desc, 300)
