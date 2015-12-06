# -*- coding: utf-8 -*-
from datetime import datetime

from vilya.config import DOMAIN
from vilya.libs.store import store
from vilya.models.project import CodeDoubanProject


class CommitStatus(object):
    def __init__(self, id, project_id, sha, state, target_url, description,
                 time, author):
        self.project_id = project_id
        self.sha = sha
        self.id = id
        self.state = state
        self.target_url = target_url
        self.description = description
        self.time = time
        self.author = author

        self.project = CodeDoubanProject.get(self.project_id)

    def as_dict(self):
        return dict(
            created_at=self.time.strftime('%Y-%m-%dT%H:%M:%S'),
            state=self.state,
            target_url=self.target_url,
            description=self.description,
            id=self.id,
            url="%s/api/%s/statuses/%s" % (
                DOMAIN, self.project.name, self.id),
            creator=self.author
        )


class CommitStatuses(object):
    """ used by QACI """

    VALID_STATE = ['pending', 'success', 'error', 'failure']

    def __init__(self, project_id, sha):
        self.project_id = project_id
        self.sha = sha

    def add(self, state, target_url, description, author):
        if state not in CommitStatuses.VALID_STATE:
            state = 'pending'

        time = datetime.now()
        params = (self.project_id, self.sha, state, target_url,
                  description, time, author)
        id = store.execute("""INSERT INTO commit_statuses
            (project_id, sha, state, target_url, description, time, author)
            VALUE
            (%s, %s, %s, %s, %s, %s, %s)
            """, params)
        store.commit()
        return CommitStatus(id, self.project_id, self.sha, state, target_url,
                            description, time, author)

    def all(self):
        rs = store.execute(
            "SELECT id, project_id, sha, state, target_url, description, "
            "time, author FROM commit_statuses WHERE project_id=%s AND "
            "sha=%s ORDER BY time DESC", (self.project_id, self.sha))
        return [CommitStatus(*r) for r in rs]

    def get(self, id):
        rs = store.execute(
            "SELECT id, project_id, sha, state, target_url, description, "
            "time, author FROM commit_statuses WHERE project_id=%s AND id=%s "
            "ORDER BY time DESC", (self.project_id, id))
        cs = [CommitStatus(*r) for r in rs]
        return cs[0] if len(cs) > 0 else None

    def latest(self):
        rs = store.execute(
            "SELECT id, project_id, sha, state, target_url, description, "
            "time, author FROM commit_statuses WHERE project_id=%s AND "
            "sha=%s ORDER BY time DESC LIMIT 1", (self.project_id, self.sha))
        cs = [CommitStatus(*r) for r in rs]
        return cs[0] if len(cs) > 0 else None
