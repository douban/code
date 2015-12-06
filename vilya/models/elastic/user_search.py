# -*- coding: utf-8 -*-
from datetime import datetime

from vilya.models.project import CodeDoubanProject
from vilya.models.user import User

from .consts import DATE_FORMAT
from .indexer import IndexEngine
from .searcher import SearchEngine


class UserSearch(object):

    @classmethod
    def delete_mapping(cls):
        result = IndexEngine.delete_mapping('user')
        return result

    @classmethod
    def search_a_phrase(cls, phrase, from_=0, size=20, sort_data=None):
        result = SearchEngine.search_a_phrase('user', phrase, from_, size,
                                              sort_data=sort_data)
        return result

    @classmethod
    def format_search_result(cls, result):
        if not SearchEngine.check_result(result):
            return []
        formatted = []
        result = result['hits']['hits']
        for r in result:
            _source = r['_source']
            sr = UserResult(
                name=_source.get('name'),
            )
            formatted.append(sr)
        return formatted

    @classmethod
    def get_user_index(cls, user):
        index_data = user.as_dict()
        badges_count = len(index_data['badges'])
        del index_data['badges']
        praises_count = len(user.get_praises())
        repos_count = len(CodeDoubanProject.get_ids(owner=user.name))
        index_data.update(  # TODO: add other necessary fields
            repos_count=repos_count,
            praises_count=praises_count,
            badges_count=badges_count,
            last_updated=datetime.now().strftime(DATE_FORMAT),  # FIXME
        )
        return index_data

    @classmethod
    def index_users(cls):
        projects = CodeDoubanProject.get_projects()
        user_names = set(project.owner_name for project in projects)
        index_data = [cls.get_user_index(User(u)) for u in user_names]
        indexes = [(data['name'].encode('hex'), data) for data in index_data]
        IndexEngine.create_index_bulk('user', indexes)

    @classmethod
    def query_user_objs(cls, size=1000):
        result = SearchEngine.query_all('user')
        if result and result.get('error'):
            return []
        total = result['hits']['total']

        name_list = []
        from_ = 0
        while from_ < total:
            result = SearchEngine.query_all('user', from_, size)
            result = SearchEngine.decode(result, ('name',))
            name_list += result
            from_ += size
        return name_list

    @classmethod
    def update_user_indexes(cls):
        old_obj_names = cls.query_user_objs()
        old_obj_names = set(name for name, in old_obj_names)
        projects = CodeDoubanProject.get_projects()
        new_obj_names = set(project.owner_name for project in projects)
        to_delete_names = old_obj_names - new_obj_names

        cls.delete_user_indexes(to_delete_names)

        index_data = [cls.get_user_index(User(u)) for u in new_obj_names]
        indexes = [(data['name'].encode('hex'), data) for data in index_data]
        IndexEngine.create_index_bulk('user', indexes)

    @classmethod
    def delete_user_indexes(cls, user_names):
        index_ids = [name.encode('hex') for name in user_names]
        IndexEngine.delete_index_bulk('user', index_ids)


class UserResult(object):

    def __init__(self, name=''):
        self.name = name
        self.user = User(name)
