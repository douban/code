# -*- coding: utf-8 -*-

from vilya.libs.validators import check_git_url
from vilya.libs.model import BaseModel, ModelField
from vilya.models.consts import (MIRROR_STATE_CLONED,
                                 MIRROR_NOT_PROXY)


class CodeDoubanMirror(BaseModel):
    __orz_table__ = "codedouban_mirror"
    url = ModelField()
    state = ModelField()
    project_id = ModelField(ModelField.KeyType.ASC)
    with_proxy = ModelField(default=MIRROR_NOT_PROXY)
    frequency = ModelField(default=0)

    class OrzMeta:
        order_combs = (("-id", ),)

    def __str__(self):
        return "Mirror: %s " % self.url

    @classmethod
    def validate(cls, repo_url):
        return check_git_url(repo_url)

    @classmethod
    def add(cls, url, state, project_id, with_proxy=MIRROR_NOT_PROXY):
        return cls.create(project_id=project_id,
                          url=url,
                          state=state,
                          with_proxy=with_proxy)

    @classmethod
    def get_by_project_id(cls, project_id):
        return cls.get(project_id=project_id)

    def update_state(self, state):
        self.state = state
        self.save()

    @property
    def is_clone_completed(self):
        return self.state == MIRROR_STATE_CLONED
