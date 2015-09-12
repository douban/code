# -*- coding: utf-8 -*-

from vilya.libs.model import BaseModel, ModelField


class ProjectWatcher(BaseModel):
    __orz_table__ = "codedouban_watches"
    user_id = ModelField(as_key=ModelField.KeyType.DESC)
    project_id = ModelField(as_key=ModelField.KeyType.DESC)

    class OrzMeta:
        id2str = True


# FIXME: primary key hook_id
class ProjectHook(BaseModel):
    __orz_table__ = "codedouban_hooks"
    hook_id = ModelField(as_key=ModelField.KeyType.DESC)
    url = ModelField()
    project_id = ModelField(as_key=ModelField.KeyType.DESC)

    class OrzMeta:
        id2str = True
