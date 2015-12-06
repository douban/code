# -*- coding: utf-8 -*-

import json
import logging

from vilya.libs.search import code_client


class IndexEngine(object):

    c = code_client
    if not c.head():
        c.put('')

    @classmethod
    def update_mapping(cls, index_type, data):
        result = cls.c.post(
            '%s/_mapping' % index_type, data=data, params={'refresh': True})
        return result

    @classmethod
    def delete_mapping(cls, index_type):
        result = cls.c.delete(
            '%s/_mapping' % index_type, params={'refresh': True})
        return result

    @classmethod
    def create_a_index(cls, index_type, index_name, data):
        result = cls.c.post(
            '%s/%s/' % (index_type, index_name), data=data,
            params={'refresh': True})
        return result

    @classmethod
    def create_index_bulk(cls, index_type, data_list, update=False,
                          bulk_count=90, body_size_limit=1000000):
        cmd = 'update' if update else 'index'
        datalen = len(data_list)
        i = 0
        while i < datalen:
            d = data_list[i:i + bulk_count]

            bulk_list = []
            for k, v in d:
                bulk_list.append({cmd: {"_id": k}})
                if update:
                    v = {'doc': v, 'doc_as_upsert': True}
                bulk_list.append(v)

            bulk_body_list = map(
                lambda x: json.dumps(x, ensure_ascii=False), bulk_list)
            bulk_body_list_len = len(bulk_body_list)
            body_size = 0
            pos = 0
            while pos < bulk_body_list_len and body_size < body_size_limit:
                body_size += len(bulk_body_list[pos])
                pos += 1
            if body_size >= body_size_limit:
                pos = pos - 1 if pos % 2 != 0 else pos - 2

            bulk_body = '\n'.join(bulk_body_list[:pos]) + '\n'
            result = cls.c.post(
                '%s/_bulk' % index_type, data=bulk_body,
                params={'refresh': True})
            logging.info('create index bulk, result: %s', result)
            # TODO: deal with error in result
            i += pos / 2

    @classmethod
    def delete_a_index(cls, index_type, index_name):
        result = cls.c.delete('%s/%s/' % (index_type, index_name))
        return result

    @classmethod
    def delete_index_bulk(cls, index_type, data_list, bulk_count=1000):
        datalen = len(data_list)
        for i in range(0, datalen, bulk_count):
            d = data_list[i:i + bulk_count]

            bulk_list = []
            for k in d:
                bulk_list.append({"delete": {"_id": k}})

            bulk_body = '\n'.join(map(
                lambda x: json.dumps(x, ensure_ascii=False), bulk_list)) + '\n'
            result = cls.c.post(
                '%s/_bulk' % index_type, data=bulk_body,
                params={'refresh': True})
