# -*- coding: utf-8 -*-
from vilya.libs.validators import check_url, check_integer
from vilya.libs.store import store


class CodeDoubanHook(object):
    def __init__(self, id, url, project_id):
        self.url = url
        self.project_id = project_id
        self.id = int(id)

    def __str__(self):
        return "Hook : %s " % self.url

    def validate(self):
        errors = []
        validators = [check_url(
            self.url, 'Url'), check_integer(self.project_id, 'Project ID')]
        for error in validators:
            if error:
                errors.append(error)
        return errors

    def destroy(self):
        store.execute(
            "delete from codedouban_hooks where hook_id=%s", (self.id,))
        store.commit()
        return self

    @classmethod
    def add(cls, url, project_id):
        hook_id = store.execute("insert into codedouban_hooks "
                                "(project_id, url) values "
                                "(%s, %s)",
                                (project_id, url))
        store.commit()
        return cls(hook_id, url, project_id)

    @classmethod
    def get_id_by_url(cls, project_id, url):
        rs = store.execute(
            'select hook_id from codedouban_hooks '
            'where project_id=%s and url=%s', (project_id, url,))
        return rs[0][0] if rs else None

    @classmethod
    def get_by_url(cls, url):
        rs = store.execute('select hook_id, url, project_id from '
                           'codedouban_hooks where url=%s', (url,))
        return cls(*rs[0]) if rs else ''
