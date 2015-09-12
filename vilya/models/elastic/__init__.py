# -*- coding: utf-8 -*-

import logging

from vilya.libs.search import code_client
from vilya.libs.htmlprocessor import html_index_content
from vilya.models.gist import Gist
from vilya.models.project import CodeDoubanProject
from vilya.models.sphinx_docs import SphinxDocs

from .searcher import SearchEngine
from .indexer import IndexEngine


class CodeSearch(object):

    c = code_client
    if not c.head():
        c.put('')

    @classmethod
    def index_a_gist(cls, id):
        gist = Gist.get(id)
        if not gist:
            return
        data = gist.as_dict()
        result = {}
        if data:
            serial = str(id)
            result = cls.c.post(
                'doc/gist_%s/' % serial, data=data, params={'refresh': True})
        return result

    @classmethod
    def delete_a_gist(cls, id):
        IndexEngine.delete_a_index('doc', 'gist_%s' % id)

    @classmethod
    def index_a_doc_file(cls, serial, data):
        result = cls.c.post(
            'doc/%s/' % serial, data=data, params={'refresh': True})
        return result

    @classmethod
    def _type_result(cls, json_raw, tp):
        dic = json_raw
        if not dic or dic.get('error') or dic['hits']['total'] == 0:
            return []
        results = []
        for e in dic['hits']['hits']:
            d = e.get(tp, {})
            results.append(d)
        return results

    @classmethod
    def search_a_phrase(cls, phrase, from_=0, size=10, project_id=None,
                        sort_data=None, doctype=None):
        highlight_data = {
            "pre_tags": ["<highlight>"],
            "post_tags": ["</highlight>"],
            "fields": {
                "content": {"number_of_fragments": 10},
                "description": {},
                "url": {},
                "author": {},
            }
        }

        filter_list = []
        if project_id:
            filter_list.append({"term": {"project_id": project_id}})
        if doctype:
            filter_list.append({"term": {"type": doctype}})
        if filter_list:
            filter_data = {"and": filter_list}
        else:
            filter_data = None

        facets_data = {
            "doctype": {
                "terms": {
                    "field": "type"
                }
            }
        }

        result = SearchEngine.search_a_phrase('doc', phrase, from_, size,
                                              filter_data=filter_data,
                                              sort_data=sort_data,
                                              highlight_data=highlight_data,
                                              facets_data=facets_data)
        return result

    @classmethod
    def format_search_result(cls, result):
        if not SearchEngine.check_result(result):
            return []
        return zip(cls._type_result(result, '_source'),
                   cls._type_result(result, 'highlight'))

    @classmethod
    def format_facets(cls, result):
        if not SearchEngine.check_result(result):
            return {}
        formatted = dict(doctype=result['facets']['doctype']['terms'])
        return formatted

    @classmethod
    def index_a_project_docs(cls, id):
        ds = DocsSearch(id)
        doc_file_dicts = ds.doc_file_datas()
        for data in doc_file_dicts:
            if data and isinstance(data, dict):
                index_filename = data['url'].replace('/', '_')
                index_filename = index_filename.replace('.', '_')
                serial = "project_%s_%s" % (id, index_filename)
                cls.index_a_doc_file(serial, data)

    @classmethod
    def delete_a_project_docs(cls, id):
        data = {
            "term": {
                "project_id": id
            }
        }
        cls.c.delete('doc/_query', data=data)


class DocsSearch(object):

    def __init__(self, project_id):
        self.project_id = project_id
        self.project = CodeDoubanProject.get(self.project_id)
        self.repo = self.project.repo

    def doc_file_datas(self):
        dicts = []
        for tab, src_paths in self._doc_infos():
            for path in src_paths:
                dicts.append(self._doc_file_as_dict(path, tab[2], tab[1]))
        return dicts

    def _doc_infos(self):
        doc_tabs = self.project.doc_tabs()
        doc_infos = []
        for tab in doc_tabs:
            try:
                tree = self.repo.get_tree("HEAD", tab[3], recursive=True)
            except Exception, err:
                logging.warning("Maybe an empty repository : %r", err)
                return []
            src_paths = [d['path'] for d in tree
                         if d['path'].endswith((".html", ".rst"))]
            doc_infos.append([tab, src_paths])
        return doc_infos

    def _doc_file_as_dict(self, path, name, doc_dir):
        last_commit = self.repo.get_last_commit("HEAD", path)
        if not last_commit:
            return
        sd = SphinxDocs(project_name=self.project.name)
        data = {
            'type': 'docs',
            'description': '',
            'author': last_commit.author.name,
            'time': last_commit.time.strftime('%Y-%m-%dT%H:%M:%S'),
            'project_id': self.project.id,
            'project_name': self.project.name,
            'doc_name': name,
            'doc_dir': doc_dir,
            'url': sd.get_url_from_path(path)
        }
        blob = self.repo.get_file('HEAD', path)
        src = blob.data or ''
        if path.endswith('.html'):
            data['content'] = html_index_content(src)
        else:
            data['content'] = src
        return data
