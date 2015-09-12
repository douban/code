# -*- coding: utf-8 -*-

from vilya.libs.search import code_client


class SearchEngine(object):

    c = code_client
    if not c.head():
        c.put('')

    @classmethod
    def check_result(cls, result):
        if result and not result.get('error'):
            return True
        return False

    @classmethod
    def decode(cls, json_raw, parse_names):
        dic = json_raw
        if not cls.check_result(dic):
            return []
        decoded = []
        for e in dic['hits']['hits']:
            d = e['_source']
            values = []
            for parse_name in parse_names:
                values.append(d.get(parse_name))
            decoded.append(values)
        return decoded

    @classmethod
    def get_count(cls, result):
        if cls.check_result(result):
            return result['hits']['total']
        return 0

    @classmethod
    def query_all(cls, index_type, from_=0, size=0):
        data = {
            'from': from_,
            'size': size,
            'query': {
                'match_all': {}
            }
        }
        result = cls.c.get('%s/_search' % index_type, data=data)
        return result

    @classmethod
    def query_by_field(cls, index_type, field_dict, from_=0, size=0):
        data = {
            'from': from_,
            'size': size,
            'query': {
                "term": field_dict,
            },
        }
        result = cls.c.get('%s/_search' % index_type, data=data)
        return result

    @classmethod
    def search_a_phrase(cls, index_type, phrase, from_=0, size=20,
                        filter_data=None, sort_data=None, highlight_data=None,
                        facets_data=None):
        data = {
            'from': from_,
            'size': size,
            "query": {
                "query_string": {
                    "query": phrase
                }
            },
        }

        if highlight_data:
            data['highlight'] = highlight_data

        if filter_data:
            filtered_query_data = {
                "filtered": {
                    "query": data['query'],
                    "filter": filter_data,
                }
            }
            data['query'] = filtered_query_data

        if sort_data:
            data['sort'] = sort_data

        if facets_data:
            data['facets'] = facets_data

        result = cls.c.get('%s/_search' % index_type, data=data)
        return result
