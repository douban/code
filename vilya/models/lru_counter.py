# -*- coding: utf-8 -*-

from vilya.libs.store import mc

MAX_PROJECT_COUNT = 50


class LRUCounter(object):
    MC_KEY_COUNT = 'lru:user:%s:project:%s'

    def __init__(self, username, target_ids):
        self.username = username
        self.target_ids = target_ids

    def mc_key(self, target_id):
        return self.MC_KEY_COUNT % (self.username, target_id)

    def travel(self, func):
        map(func, self.target_ids)

    def use(self, target_id):
        if target_id in self.target_ids:
            self.travel(self._incr)
            self._clear(target_id)

    def count(self, target_id):
        return mc.get(self.mc_key(target_id))

    def sort(self, is_desc=False):
        self.target_ids.sort(key=lambda x: self.count(x),
                             reverse=is_desc)
        return self.target_ids

    def dump(self):
        for id_ in self.target_ids:
            print self.count(id_)

    def _incr(self, target_id):
        if self.count(target_id) is None:
            self._clear(target_id)
        mc.incr(self.mc_key(target_id), 1)
        if self.count(target_id) > MAX_PROJECT_COUNT:
            self._set(target_id, MAX_PROJECT_COUNT)

    def _set(self, target_id, value):
        mc.set(self.mc_key(target_id), value)

    def _clear(self, target_id):
        self._set(target_id, 0)


class ProjectOwnLRUCounter(LRUCounter):
    MC_KEY_COUNT = 'lru:project_own:user:%s:project:%s'

    def __init__(self, username, target_ids=None):
        if not target_ids:
            from vilya.models.project import CodeDoubanProject
            target_ids = CodeDoubanProject.get_ids(owner=username)
        super(ProjectOwnLRUCounter, self).__init__(username, target_ids)


class ProjectWatchLRUCounter(LRUCounter):
    MC_KEY_COUNT = 'lru:project_watch:user:%s:project:%s'

    def __init__(self, username, target_ids=None):
        if not target_ids:
            from vilya.models.project import CodeDoubanProject
            target_ids = CodeDoubanProject.get_watched_others_ids_by_user(
                user=username)
        super(ProjectWatchLRUCounter, self).__init__(username, target_ids)
