# -*- coding: utf-8 -*-
import string

from vilya.libs.store import store
from vilya.libs.text import trunc_utf8
from dispatches import dispatch
from vilya.models.consts import COMMIT_COMMENT_UID_PATTERN

_allowed_in_field_names = string.ascii_letters + string.digits + ' '
_DEFLIMIT = 50
_DEFORDER = 'asc'


def _safe_field(field_name):
    if not all(c in _allowed_in_field_names for c in field_name):
        raise Exception("Unsafe field name: %s" % field_name)
    return True


def _make_update_setters(changes):
    fields = changes.keys()
    assert all(_safe_field(f) for f in fields)
    setters = ', '.join("`%s` = %%s" % f for f in fields)
    values = [changes[k] for k in fields]
    return setters, values


def add(proj_id, ref, author, content):
    comment_id = store.execute("insert into codedouban_comments "
                               "(project_id, ref, author, content) "
                               "values (%s, %s, %s, %s)",
                               (proj_id, ref, author, content))
    if not comment_id:
        store.rollback()
        raise Exception("Unable to insert new comment")
    store.commit()
    return comment_id


def get(comment_id):
    rs = store.execute(
        "select comment_id, project_id, ref, author, content, created "
        "from codedouban_comments where comment_id = %s", (comment_id,))
    return rs and rs[0] or None


def _gets(field, value, order=_DEFORDER, start=0, limit=_DEFLIMIT):
    assert field in ('project_id', 'ref', 'author')
    rs = store.execute(
        "select comment_id from codedouban_comments where %s = %%s "
        "order by comment_id %s limit %%s, %%s" % (field, order),
        (value, start, limit))
    return [cid for cid, in rs]


def gets_by_project(project_id, order=_DEFORDER, start=0, limit=_DEFLIMIT):
    return _gets('project_id', project_id, order, start, limit)


def gets_by_ref(ref, order=_DEFORDER, start=0, limit=_DEFLIMIT):
    return _gets('ref', ref, order, start, limit)


def gets_by_proj_and_ref(proj_id, ref, order=_DEFORDER, start=0,
                         limit=_DEFLIMIT):
    assert order in ('asc', 'desc')
    rs = store.execute(
        "select comment_id from codedouban_comments where project_id = %%s "
        "and ref = %%s order by comment_id %s  limit %%s, %%s" % order,
        (proj_id, ref, start, limit))
    return [cid for cid, in rs]


def gets_by_author(author, order=_DEFORDER, start=0, limit=_DEFLIMIT):
    return _gets('author', author, order, start, limit)


def delete(comment_id):
    n = store.execute("delete from codedouban_comments "
                      "where comment_id = %s", (comment_id,))
    if n:
        store.commit()
        return True


def latest():
    rs = store.execute("select comment_id from codedouban_comments "
                       "order by comment_id asc", ())
    return [cid for cid, in rs]


def update(comment_id, changes):
    assert changes, "Must have some changes to propose"
    assert all(k in (
        'content', ) for k in changes.keys()), "Can only update some fields"
    setters, values = _make_update_setters(changes)
    n = store.execute(
        "update codedouban_comments set %s "
        "where comment_id = %%s" % setters, values + [comment_id])
    if n == 0:
        store.rollback()
        raise Exception("Comment %s not found, not updated" % comment_id)
    if n > 1:
        store.rollback()
        raise Exception(
            "Weird: more than one comment found for id %s, not updated".format(
                comment_id))
    store.commit()

# ORM wrapper


class Comment(object):
    def __init__(self, comment_id, project_id, ref, author, content, created):
        self.comment_id = comment_id
        self.project_id = project_id
        self.ref = ref
        self.author = author
        self.content = content
        self.created = created

        # 兼容属性名
        self.id = comment_id

    def __repr__(self):
        return "Comment(%s, %s, %s, ...)" % (self.comment_id,
                                             self.project_id, self.ref)

    def __eq__(self, other):
        return type(self) == type(other) \
            and self.comment_id == other.comment_id

    @property
    def short_content(self):
        content = self.content
        if content:
            return trunc_utf8(content, 30)

    @property
    def uid(self):
        return COMMIT_COMMENT_UID_PATTERN % self.id

    # no use
    def to_dict(self):
        return self.__dict__

    @classmethod
    def add(cls, project, ref, author, content, commit_author=None):
        new_comment_id = add(project.id, ref, author, content)
        new_comment = cls.get(new_comment_id)

        dispatch('comment', data={
            'comment': new_comment,
            'commit_author': commit_author, })

        # for commit comments rewrite to pr
        dispatch('comment_actions', data={
            'type': 'commit_comment',
            'comment': new_comment,
            'commit_author': commit_author,
        })

        return new_comment

    @classmethod
    def get(cls, comment_id):
        c = get(comment_id)
        return cls(*c) if c else None

    @classmethod
    def delete(cls, comment_id):
        return delete(comment_id)

    def update(self, content):
        update(self.comment_id, {'content': content})
        self.content = content

    @classmethod
    def gets_by_project(cls, project_id, order=_DEFORDER, start=0,
                        limit=_DEFLIMIT):
        return cls._gets(gets_by_project(project_id, order, start, limit))

    @classmethod
    def gets_by_ref(cls, ref, order=_DEFORDER, start=0, limit=_DEFLIMIT):
        return cls._gets(gets_by_ref(ref, order, start, limit))

    @classmethod
    def gets_by_proj_and_ref(cls, proj, ref, order=_DEFORDER, start=0,
                             limit=_DEFLIMIT):
        return cls._gets(gets_by_proj_and_ref(proj, ref, order, start, limit))

    @classmethod
    def gets_by_author(cls, author, order=_DEFORDER, start=0, limit=_DEFLIMIT):
        return cls._gets(gets_by_author(author, order, start, limit))

    @classmethod
    def _gets(cls, comment_ids):
        return [cls.get(cid) for cid in comment_ids]
