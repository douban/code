# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from vilya.models.project import CodeDoubanProject
from vilya.models.user import User

from .consts import DATE_FORMAT
from .indexer import IndexEngine
from .searcher import SearchEngine


class RepoSearch(object):

    @classmethod
    def delete_mapping(cls):
        result = IndexEngine.delete_mapping('repo')
        return result

    @classmethod
    def search_a_phrase(cls, phrase, from_=0, size=20, sort_data=None):
        highlight_data = {
            "fields": {
                "description": {"number_of_fragments": 0}
            }
        }

        if not sort_data:
            sort_data = [
                {"forked_count": "desc"},
                {"watched_count": "desc"},
                "_score",
            ]

        result = SearchEngine.search_a_phrase('repo', phrase, from_, size,
                                              sort_data=sort_data,
                                              highlight_data=highlight_data)
        return result

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
                logging.error('No highlight for %s', _source)
                hl_description = ''
            sr = RepoResult(
                id=_source.get('id'),
                last_updated_str=_source.get('last_updated'),
                hl_description=hl_description,
            )
            formatted.append(sr)
        return formatted

    @classmethod
    def get_repo_index_from_project(cls, project):
        fork_from = project.get_forked_from()
        fork_from = fork_from.name if fork_from else ''
        last_commit = project.repo.get_last_commit('HEAD')
        commit_time = last_commit.commit_time if last_commit else project.time
        index_data = dict(
            id=str(project.id),
            name=project.name,
            owner=project.owner_name,
            description=project.summary,
            url=project.url,
            language=project.language,
            fork_from=fork_from,
            forked_count=CodeDoubanProject.get_forked_count(project.id),
            watched_count=CodeDoubanProject.get_watched_count(project.id),
            create_time=project.time.strftime(DATE_FORMAT),
            last_updated=commit_time.strftime(DATE_FORMAT),
        )
        return index_data

    @classmethod
    def index_repos(cls):
        projects = CodeDoubanProject.get_projects(sortby='sumup')
        index_data = [cls.get_repo_index_from_project(project)
                      for project in projects]
        indexes = [(data['id'], data) for data in index_data]
        IndexEngine.create_index_bulk('repo', indexes)

    @classmethod
    def query_repo_objs(cls, size=1000):
        result = SearchEngine.query_all('repo')
        if result and result.get('error'):
            return []
        total = result['hits']['total']

        id_list = []
        from_ = 0
        while from_ < total:
            result = SearchEngine.query_all('repo', from_, size)
            result = SearchEngine.decode(result, ('id',))
            id_list += result
            from_ += size
        return id_list

    @classmethod
    def update_repo_indexes(cls):
        old_obj_ids = cls.query_repo_objs()
        old_obj_ids = [id for id, in old_obj_ids]
        new_obj_ids = CodeDoubanProject.get_project_ids_sortby_sumup()
        new_objs = CodeDoubanProject.gets(new_obj_ids)
        to_delete_ids = set(old_obj_ids) - set(new_obj_ids)

        cls.delete_repo_indexes(to_delete_ids)

        index_data = [cls.get_repo_index_from_project(project)
                      for project in new_objs]
        indexes = [(data['id'], data) for data in index_data]
        IndexEngine.create_index_bulk('repo', indexes)

    @classmethod
    def delete_repo_indexes(cls, project_ids):
        index_ids = [str(id) for id in project_ids]
        IndexEngine.delete_index_bulk('repo', index_ids)


class RepoResult(object):

    def __init__(self, id='', last_updated_str='', hl_description=''):
        self.id = str(id)
        self.project = CodeDoubanProject.get(id)
        self.name = self.project.name
        self.owner = User(self.project.owner_name)
        self.last_updated = datetime.strptime(
            last_updated_str, DATE_FORMAT) if last_updated_str \
            else self.project.time
        self.create_time = self.project.time
        self.description = self.project.summary
        self.url = self.project.url
        self.language = self.project.language
        self.fork_from = self.project.get_forked_from()
        self.forked_count = CodeDoubanProject.get_forked_count(self.project.id)
        self.watched_count = CodeDoubanProject.get_watched_count(
            self.project.id)
        self.hl_description = hl_description or self.description
