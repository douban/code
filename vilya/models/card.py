# -*- coding: utf-8 -*-

from vilya.models import ModelField, BaseModel
from vilya.models.counter import Counter


class Card(BaseModel):
    __table__ = "cards"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField(default='')
    position = ModelField()
    number = ModelField(as_key=ModelField.KeyType.DESC)
    board_id = ModelField(as_key=ModelField.KeyType.DESC)
    project_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)
    closer_id = ModelField(as_key=ModelField.KeyType.DESC)
    closed_at = ModelField()
    archiver_id = ModelField(as_key=ModelField.KeyType.DESC)
    archived_at = ModelField()

    @classmethod
    @BaseModel.transaction
    def create_pull(cls, **kw):
        from vilya.models.pull import Pull
        if 'card_id' not in kw:
            project_id = kw['project_id']
            number = ProjectCardCounter.incr(project_id=project_id)
            kw['number'] = number
            card = cls.create(**kw)
            del kw['number']
            del kw['board_id']
            del kw['project_id']
            kw['card_id'] = card.id
        pull = Pull.create(**kw)
        return pull

    @property
    def pull(self):
        from vilya.models.pull import Pull
        pull = Pull.get(card_id=self.id)
        return pull


ProjectCardCounter = Counter('project_card_counters')
