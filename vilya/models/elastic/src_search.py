# -*- coding: utf-8 -*-

import re
import logging
from datetime import datetime
from urlparse import urljoin
from collections import defaultdict

from vilya.models.project import CodeDoubanProject
from vilya.models.user import User
from vilya.libs import consts
from vilya.libs.text import highlight_code


from .consts import DATE_FORMAT, SRC_SIZE_LIMIT
from .indexer import IndexEngine
from .searcher import SearchEngine


class SrcSearch(object):

    @classmethod
    def update_mapping(cls):
        data = {
            "src": {
                "properties": {
                    "project": {
                        "type": "multi_field",
                        "fields": {
                            "project": {
                                "type": "string",
                                "index": "analyzed"
                            },
                            "raw": {
                                "type": "string",
                                "index": "not_analyzed"
                            }
                        }
                    },
                    "owner": {
                        "type": "multi_field",
                        "fields": {
                            "owner": {
                                "type": "string",
                                "index": "analyzed"
                            },
                            "raw": {
                                "type": "string",
                                "index": "not_analyzed"
                            }
                        }
                    },
                    "committer": {
                        "type": "multi_field",
                        "fields": {
                            "committer": {
                                "type": "string",
                                "index": "analyzed"
                            },
                            "raw": {
                                "type": "string",
                                "index": "not_analyzed"
                            }
                        }
                    },
                    "language": {
                        "type": "multi_field",
                        "fields": {
                            "language": {
                                "type": "string",
                                "index": "analyzed"
                            },
                            "raw": {
                                "type": "string",
                                "index": "not_analyzed"
                            }
                        }
                    },
                }
            }
        }
        result = IndexEngine.update_mapping('src', data)
        return result

    @classmethod
    def delete_mapping(cls):
        result = IndexEngine.delete_mapping('src')
        return result

    @classmethod
    def query_by_project(cls, project_name, from_=0, size=0):
        field_dict = {
            "project.raw": project_name,
        }
        result = SearchEngine.query_by_field('src', field_dict, from_, size)
        return result

    @classmethod
    def search_a_phrase(cls, phrase, from_=0, size=20, project_id=None,
                        sort_data=None, language=None):
        highlight_data = {
            "fields": {
                "content": {"number_of_fragments": 0}
            }
        }

        filter_list = []

        # FIXME: use project_id field
        project = CodeDoubanProject.get(project_id) if project_id else None
        if project:
            filter_list.append({"term": {"project.raw": project.name}})

        if language:
            filter_list.append({"term": {"language.raw": language}})

        if filter_list:
            filter_data = {"and": filter_list}
        else:
            filter_data = None

        if not sort_data:
            if project_id:
                sort_data = ['rank', '_score']
            else:
                sort_data = [
                    "rank",
                    "_score",
                    {"project_rank": "desc"},
                    {"last_updated": "desc"},
                ]

        facets_data = {
            "language": {
                "terms": {
                    "field": "language.raw"
                }
            }
        }

        result = SearchEngine.search_a_phrase('src', phrase, from_, size,
                                              sort_data=sort_data,
                                              filter_data=filter_data,
                                              highlight_data=highlight_data,
                                              facets_data=facets_data)
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
                hl_content = r['highlight']['content'][0]
            except:
                logging.error('No highlight content for %s', _source)
                hl_content = ''

            project_name = _source.get('project')
            if not project_name:
                logging.error('Invaild index: %s', _source)
                continue

            project = CodeDoubanProject.get_by_name(project_name)
            if not project:
                logging.error(
                    'Invaild index: %s, project: %s', (_source, project_name))
                continue

            sr = SrcResult(
                id=_source.get('id'),
                commit_id=_source.get('commit'),
                name=_source.get('name'),
                project_name=_source.get('project'),
                owner_name=_source.get('owner'),
                last_updated_str=_source.get('last_updated'),
                content=_source.get('content'),
                language=_source.get('language'),
                hl_content=hl_content,
            )
            formatted.append(sr)
        return formatted

    @classmethod
    def format_facets(cls, result):
        if not SearchEngine.check_result(result):
            return {}
        formatted = dict(language=result['facets']['language']['terms'])
        return formatted

    @classmethod
    def get_src_index_from_project(cls, project, repo, src_data):
        obj_id = src_data[0]
        obj = repo.repo.show(obj_id)
        index_data = {}
        if not obj['binary']:
            obj_name = src_data[1]['path']
            obj_size = obj['size']
            commit_id = src_data[1]['commit']
            commit_time = src_data[1]['commit_time']
            committer = src_data[1]['committer'].encode('utf8')
            rank = src_data[1]['rank']
            # don't fully index a large src
            obj_data = obj['data'] if obj_size < SRC_SIZE_LIMIT else obj['data'][:SRC_SIZE_LIMIT]  # noqa
            index_data = dict(
                id=obj_id,
                commit=commit_id,
                commit_time=commit_time.strftime(DATE_FORMAT),
                committer=committer,
                name=obj_name,
                project=project.name,
                owner=project.owner_name,
                content=obj_data,
                last_updated=datetime.now().strftime(DATE_FORMAT),
                rank=rank,
                size=obj_size,
                language=cls.get_src_language(obj_name),
            )
        return index_data

    @classmethod
    def get_src_language(cls, path):
        filename = path.split('/')[-1]  # strip directories
        pos = filename.rfind('.')
        if pos == -1 or pos == 0:
            ext = ''
        else:
            ext = filename[pos + 1:]

        if not ext:
            language = consts.LANGUAGES_WITHOUT_EXT.get(filename)
        else:
            language = consts.LANGUAGES.get(ext)

        return language or 'Text'

    @classmethod
    def _get_all_revobjs_with_rank(cls, project):
        result = project.repo.get_all_src_objects()
        # calc rank base on size
        result_by_name = defaultdict(list)
        for obj_id, data in result.iteritems():
            result_by_name[data['path']].append((obj_id, data['size']))
        for name, data in result_by_name.iteritems():
            data.sort(key=lambda x: x[1], reverse=True)
            for seq, obj_data in enumerate(data):
                result[obj_data[0]]['rank'] = seq + 1

        return result

    @classmethod
    def get_src_indexes_from_project(cls, project):
        rev_objects = cls._get_all_revobjs_with_rank(project)
        repo = project.repo
        indexes = []
        for data in rev_objects.iteritems():
            index_data = cls.get_src_index_from_project(project, repo, data)
            if not index_data:
                continue
            index_id = str(project.id) + index_data['id']
            indexes.append((index_id, index_data))
        return indexes

    @classmethod
    def index_a_project(cls, project):
        indexes = cls.get_src_indexes_from_project(project)

        # FIXME: change project_rank algrithm
        project_rank = CodeDoubanProject.get_forked_count(project.id)
        for id, data in indexes:
            data['project_rank'] = project_rank

        IndexEngine.create_index_bulk('src', indexes)

    @classmethod
    def query_a_project_objs(cls, project_name, fields, size=1000):
        result = cls.query_by_project(project_name)
        if result and result.get('error'):
            return []
        total = result['hits']['total']

        id_list = []
        from_ = 0
        while from_ < total:
            result = cls.query_by_project(project_name, from_, size)
            result = SearchEngine.decode(result, fields)
            id_list += result
            from_ += size
        return id_list

    @classmethod
    def update_a_project_index(cls, project):
        rev_objs = cls._get_all_revobjs_with_rank(project)
        rev_obj_ids = set(rev_objs)
        rev_obj_id_stats = set((id, data['rank'])
                               for id, data in rev_objs.iteritems())

        old_obj_id_stats = cls.query_a_project_objs(
            project.name, fields=('id', 'rank'))
        old_obj_ids = set(data[0] for data in old_obj_id_stats)
        old_obj_id_stats = set(tuple(i) for i in old_obj_id_stats)

        to_delete_ids = old_obj_ids - rev_obj_ids
        to_add_ids = rev_obj_ids - old_obj_ids
        to_update_id_stats = rev_obj_id_stats - old_obj_id_stats
        to_update_id_stats = [data for data in to_update_id_stats
                              if data[0] not in to_add_ids]

        index_ids = [str(project.id) + i for i in to_delete_ids]
        IndexEngine.delete_index_bulk('src', index_ids)

        # FIXME: remove this bulk update support
        to_add_ids |= set(data[0] for data in to_update_id_stats)

        repo = project.repo
        indexes = []
        for i in to_add_ids:
            index_data = cls.get_src_index_from_project(
                project, repo, (i, rev_objs[i]))
            if index_data:
                index_id = str(project.id) + i
                indexes.append((index_id, index_data))
        IndexEngine.create_index_bulk('src', indexes)

        # FIXME: uncomment this if bulk update support
        # indexes = []
        # for id, rank in to_update_id_stats:
            # index_id = str(project.id) + id
            # index_data = dict(rank=rank)
            # indexes.append((index_id, index_data))
        # IndexEngine.create_index_bulk('src', indexes, update=True,
        # bulk_count=500)

    @classmethod
    def delete_a_project_index(cls, project):
        old_obj_ids = [i for i, in cls.query_a_project_objs(
            project.name, fields=('id',))]
        index_ids = [str(project.id) + i for i in old_obj_ids]
        IndexEngine.delete_index_bulk('src', index_ids)

    @classmethod
    def update_a_project_index_rank(cls, project, project_rank):
        old_obj_id_stats = cls.query_a_project_objs(
            project.name, fields=('id', ))
        indexes = []
        for id, in old_obj_id_stats:
            index_id = str(project.id) + id
            index_data = dict(project_rank=project_rank)
            indexes.append((index_id, index_data))
        IndexEngine.create_index_bulk('src', indexes, update=True, bulk_count=500)


class SrcResult(object):

    def __init__(self, id='', commit_id='', name='', project_name='',
                 owner_name='', last_updated_str='', content='', hl_content='',
                 language=''):
        self.id = str(id)
        self.commit_id = str(commit_id)
        self.name = name
        self.project = CodeDoubanProject.get_by_name(project_name)
        self.owner = User(owner_name)
        self.last_updated = datetime.strptime(
            last_updated_str, DATE_FORMAT) if last_updated_str else self.project.time
        self.content = content
        self.hl_content = hl_content or content
        self.language = language

        self.path_url = urljoin(urljoin(
            self.project.url, 'blob/%s/' % self.commit_id), self.name)

    def snippet(self):
        # TODO: fragment
        raw_content_lines = list(enumerate(self.content.split('\n')))
        hl_content_lines = list(enumerate(self.hl_content.split('\n')))
        fragment_lines = set(raw_content_lines) - set(hl_content_lines)
        line_nums = sorted([i for i, c in fragment_lines])

        max_lines = 10
        begin = line_nums[0] if line_nums else 0
        end = line_nums[-1] if line_nums else max_lines
        delta = min(max_lines, end - begin + 1)

        snippets = [c for i, c in raw_content_lines[begin:begin + delta]]
        hl_name = self.name
        for line in snippets:
            if len(line) > 512:
                # don't highlight long line
                hl_name = 'xxx'
        highlighted = highlight_code(
            hl_name, '\n'.join(snippets), linenostart=begin + 1).decode('utf8')
        phrases = re.findall(
            ur'<em>(\w+)</em>', self.hl_content.decode('utf8'),
            flags=re.UNICODE)
        pattern = ur'|'.join(set(phrases))
        if pattern:
            pattern = ur'(%s)(?![^<>]*>)' % pattern
            highlighted = re.sub(
                pattern, ur'<em>\g<0></em>', highlighted,
                flags=re.UNICODE).encode('utf8')
        else:
            logging.debug('Fail to highlight keywords in search result. \nraw_content: \n%s\n\nhl_content: \n%s',  # noqa
                          self.content, self.hl_content)
        return highlighted
