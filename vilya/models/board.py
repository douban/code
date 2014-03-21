# -*- coding: utf-8 -*-

from vilya.models import ModelField, BaseModel
from vilya.models.counter import Counter


class Board(BaseModel):
    __table__ = "boards"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField(default='')
    role = ModelField(as_key=ModelField.KeyType.DESC)
    position = ModelField(default='1')
    number = ModelField(as_key=ModelField.KeyType.DESC)
    project_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)
    archiver_id = ModelField(as_key=ModelField.KeyType.DESC)
    archived_at = ModelField()

    def __repr__(self):
        return "<Board,%s>" % self.id


ProjectBoardCounter = Counter('project_board_counters')
