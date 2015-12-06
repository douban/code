# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from vilya.libs.store import mc, cache
from vilya.libs.store import store

MC_KEY_TAG_TYPE_IDS_BY_TAG_ID = "code:tags:type_ids:by:tag_id:%s"
MC_KEY_TAG_IDS_BY_TARGET_ID_AND_TYPE = "code:tag_ids:by:target_id:%s:type:%s"
ONE_DAY = 60 * 60 * 24


# TODO: table `tagname` should be renamed `tags`
# TODO: TagName should be renamed Tag
class TagName(object):

    def __init__(self, id, name, author_id, created_at, target_type,
                 target_id, hex_color):
        self.id = id
        self.name = name
        self.author_id = author_id
        self.created_at = created_at
        self.target_type = target_type
        self.target_id = target_id
        self.hex_color = hex_color
        self._group_uid = None

    @property
    def group_uid(self):
        if self._group_uid is None:
            uid = 'used'
            name = self.name
            if ':' in name:
                if self.name.startswith('type:'):
                    uid = 'type'
                elif self.name.startswith('stage:'):
                    uid = 'stage'
                elif self.name.startswith('priority:'):
                    uid = 'priority'
            self._group_uid = uid
        return self._group_uid

    @classmethod
    def add(cls, name, author_id, target_type, target_id, color='cccccc'):
        # TODO: check tag name
        time = datetime.now()
        tagname_id = store.execute(
            "insert into tag_names(name, author_id, created_at, target_type, "
            "target_id, hex_color) values ( % s, % s, NULL, % s, % s, % s) ",
            (name, author_id, target_type, target_id, color))
        store.commit()
        return cls(
            tagname_id, name, author_id, time, target_type, target_id, color)

    @classmethod
    def gets(cls):
        tags = []
        rs = store.execute(
            "select id, name, author_id, created_at, target_type, target_id, "
            "hex_color from tag_names")
        for r in rs:
            tags.append(cls(*r))
        return tags

    @classmethod
    def get_by_name_and_target_id(cls, name, target_type, target_id):
        rs = store.execute(
            "select id, name, author_id, created_at, target_type, target_id, "
            "hex_color from tag_names "
            "where name=%s and target_type=%s and target_id=%s",
            (name, target_type, target_id))
        if rs and rs[0]:
            return cls(*rs[0])

    @classmethod
    def get_by_id(cls, id):
        rs = store.execute(
            "select id, name, author_id, created_at, target_type, target_id, "
            "hex_color from tag_names "
            "where id=%s", (id,))
        if rs and rs[0]:
            return cls(*rs[0])

    def _check_tag_is_in_use(self):
        rs = store.execute(
            "select id from tags"
            "where tag_id=%s", (self.id,))
        if rs and rs[0]:
            return True
        return False

    def delete(self):
        n = store.execute(
            "delete from tag_names "
            "where id=%s", (self.id,))
        if n:
            store.commit()
            return True

    @property
    def project_issue_ids(self):
        if self.target_type == TAG_TYPE_PROJECT_ISSUE:
            tags = Tag.gets_by_tag_id(self.id)
            return [t.type_id for t in tags]
        return []

    @classmethod
    def get_project_issue_tag(cls, name, project):
        tag_name = cls.get_by_name_and_target_id(
            name, TAG_TYPE_PROJECT_ISSUE, project.id)
        return tag_name

    @classmethod
    def get_target_tags(cls, target_type, target_id):
        rs = store.execute(
            "select id, name, author_id, created_at, target_type, target_id, "
            "hex_color from tag_names where target_type=%s and target_id=%s",
            (target_type, target_id))
        return [cls(*_) for _ in rs] if rs else []

    def update_name(self, name):
        store.execute("update tag_names set name=%s where id=%s",
                      (name, self.id))
        store.commit()
        self.name = name

    def update_color(self, color):
        store.execute("update tag_names set hex_color=%s where id=%s",
                      (color, self.id))
        store.commit()
        self.hex_color = color


# TODO: table `tags` should be renamed `target_tags` or `type_tags`
# TODO: Tag should be TargetTag or TypeTag or KindTag
class Tag(object):

    def __init__(self, id, tag_id, type, type_id, author_id, created_at,
                 target_id):
        self.id = id
        self.tag_id = tag_id
        self.type = type
        self.type_id = type_id
        self.author_id = author_id
        self.created_at = created_at
        self.target_id = target_id

    @property
    def name(self):
        tag = TagName.get_by_id(self.tag_id)
        return tag.name

    # TagName
    @property
    def tagname(self):
        return TagName.get_by_id(self.tag_id)

    @classmethod
    def add(cls, tag_id, type, type_id, author_id, target_id):
        time = datetime.now()
        issue_tag_id = store.execute(
            "insert into tags "
            "(tag_id, type_id, type, author_id, created_at, target_id) "
            "values (%s, %s, %s, %s, NULL, %s)",
            (tag_id, type_id, type, author_id, target_id))
        store.commit()
        tag = cls(issue_tag_id, tag_id, type,
                  type_id, author_id, time, target_id)
        if tag:
            tag._clean_cache()
        return tag

    @classmethod
    def get_type_tags(cls, type, type_id=None, author_id=None):
        tags = []
        sql = ("select id, tag_id, type, type_id, author_id, created_at, "
               "target_id from tags where type=%s ")
        params = [type]
        if type_id:
            sql = sql + "and type_id=%s "
            params.append(type_id)
        if author_id:
            sql = sql + "and author=%s "
            params.append(author_id)
        rs = store.execute(sql, tuple(params))
        for r in rs:
            tags.append(cls(*r))
        return tags

    def _clean_cache(self):
        mc.delete(MC_KEY_TAG_TYPE_IDS_BY_TAG_ID % self.tag_id)
        mc.delete(MC_KEY_TAG_IDS_BY_TARGET_ID_AND_TYPE %
                  (self.target_id, self.type))

    @classmethod
    def gets_by_issue_id(cls, issue_id, type):
        return cls.get_type_tags(type, issue_id)

    @classmethod
    def gets_by_tag_id(cls, tag_id):
        rs = store.execute(
            "select id, tag_id, type, type_id, author_id, created_at, "
            "target_id from tags where tag_id=%s ", tag_id)
        return [cls(*r) for r in rs]

    @classmethod
    @cache(MC_KEY_TAG_IDS_BY_TARGET_ID_AND_TYPE % (
        '{target_id}', '{type}'), expire=ONE_DAY)
    def _gets_by_target_id(cls, target_id, type):
        sql = ("select id, tag_id, type, type_id, author_id, created_at, "
               "target_id from tags where type=%s and target_id=%s")
        rs = store.execute(sql, (type, target_id))
        return rs

    @classmethod
    def gets_by_target_id(cls, type, target_id):
        rs = cls._gets_by_target_id(target_id, type)
        return [cls(*r) for r in rs]

    @classmethod
    @cache(MC_KEY_TAG_TYPE_IDS_BY_TAG_ID % '{tag_id}', expire=60 * 60 * 24)
    def get_type_ids_by_tag_id(cls, tag_id):
        sql = ("select id, tag_id, type, type_id, author_id, created_at, "
               "target_id from tags where tag_id=%s")
        rs = store.execute(sql, tag_id)
        tags = [cls(*r) for r in rs]
        return [t.type_id for t in tags if t]

    @classmethod
    def get_by_type_id_and_tag_id(cls, type, type_id, tag_id):
        rs = store.execute(
            "select id, tag_id, type, type_id, author_id, created_at, "
            "target_id from tags where type=%s and type_id=%s and tag_id=%s ",
            (type, type_id, tag_id))
        if rs and rs[0]:
            return cls(*rs[0])

    @classmethod
    def add_to_issue(cls, tag_id, type, issue_id, author_id, target_id):
        return cls.add(tag_id, type, issue_id, author_id, target_id)

    @classmethod
    def add_to_gist(cls, tag_id, gist_id, author_id, target_id):
        return cls.add(tag_id, TAG_TYPE_GIST, gist_id, author_id, target_id)

    def delete(self):
        n = store.execute(
            "delete from tags "
            "where id=%s", self.id)
        self._clean_cache()
        if n:
            store.commit()
            return True

    @classmethod
    def gets(cls):
        sql = ("select id, tag_id, type, type_id, author_id, created_at, "
               "target_id from tags")
        rs = store.execute(sql)
        return [cls(*r) for r in rs]

    @classmethod
    def get_type_ids_by_name_and_target_id(cls, type, name, target_id):
        tag_name = TagName.get_by_name_and_target_id(name, type, target_id)
        return cls.get_type_ids_by_tag_id(tag_name.id) if tag_name else []

    @classmethod
    def get_type_ids_by_names_and_target_id(cls, type, names, target_id):
        issue_ids = []
        for name in names:
            issue_ids.append(
                cls.get_type_ids_by_name_and_target_id(type, name, target_id))
        return reduce(lambda x, y: set(x) & set(y), issue_ids)


# tag target type list
TAG_TYPE_PROJECT_ISSUE = 1
TAG_TYPE_TEAM_ISSUE = 2
TAG_TYPE_GIST = 3
TAG_TYPE_FAIR_ISSUE = 4


class TagMixin(object):

    @property
    def tag_type(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def tags(self):
        return self.get_tags()

    def get_tags(self):
        all_tags = TagName.get_target_tags(self.tag_type, self.id)
        return all_tags

    def get_group_tags(self, selected_names):
        group_tags = {}
        all_tags = TagName.get_target_tags(self.tag_type, self.id)
        for tag in all_tags:
            if tag.group_uid not in group_tags:
                group_tags[tag.group_uid] = []
            if tag.name in selected_names:
                group_tags[tag.group_uid].append((tag, 0, 'selected'))
            else:
                group_tags[tag.group_uid].append((tag, 0, 'unselected'))
        return group_tags
