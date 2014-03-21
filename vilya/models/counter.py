# -*- coding: utf-8 -*-

from vilya.libs.store import store


class Counter(object):

    def __init__(self, table_name):
        self.table_name = table_name

    def _sql_statement(self, keyword, fields, concat_by=','):
        if len(fields) == 0:
            return "", ()
        prefix, values = zip(*fields)
        return keyword + " " + (concat_by.join(prefix)), values

    def incr(self, **kw):
        if 'counter' in kw:
            count = kw['counter']
        else:
            count = None
        kw['counter'] = count if count else 1
        set_sql, v = self._sql_statement('SET',
                                         [("%s=%%s" % kv[0]
                                           if kv[0] != 'counter'
                                           else "counter=LAST_INSERT_ID(%s)",
                                           kv[1]) for kv in kw.items()],
                                         ',')
        if count and count >= 0:
            statement = "insert into %s %s on duplicate key update " \
                "counter=LAST_INSERT_ID(%%s)" % (self.table_name, set_sql)
            v = v + (count, )
        else:
            statement = "insert into %s %s on duplicate key update " \
                "counter=LAST_INSERT_ID(counter+1)" % (self.table_name,
                                                       set_sql)
        id = store.execute(statement, v)
        return id

    def incr_trans(self, **kw):
        id = self.incr(**kw)
        store.commit()
        return id
