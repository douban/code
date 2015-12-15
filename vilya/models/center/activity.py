# -*- coding: utf-8 -*-
import json
from vilya.libs.text import trunc_utf8
from vilya.libs.model import BaseModel, ModelField

TYPE_DEFAULT = 0  # 人肉
TYPE_DEPLOYMENT = 1  # 上线
TYPE_MONITOR = 2  # 监控
TYPE_STATISTIC = 3  # 统计
TYPE_CONFIGURATION = 4  # 配置


class Activity(BaseModel):
    __orz_table__ = "center_activities"
    title = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField()
    type = ModelField(as_key=ModelField.KeyType.ONLY_INDEX)
    creator_id = ModelField(as_key=ModelField.KeyType.ONLY_INDEX)
    created_at = ModelField(auto_now_create=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%S+0800')
        }

    @property
    def rendered_description(self):
        from vilya.libs.text import render_markdown
        description = self.description
        if description:
            description = render_desc(self.type, description)
            return render_markdown(description)
        return ''

    @property
    def short_description(self):
        if self.description:
            return trunc_utf8(self.description, 80)
        return ''

    @property
    def url(self):
        return 'activities/%s' % self.id


def render_desc(type, description):
    if type == TYPE_DEFAULT:
        return description
    if type == TYPE_DEPLOYMENT:
        return render_deployment_desc(description)
    if type == TYPE_MONITOR:
        return render_monitor_desc(description)
    if type == TYPE_CONFIGURATION:
        return description
    if type == TYPE_STATISTIC:
        return description
    return description


DEPLOYMENT_DESCRIPTION_V1 = """
* Current Version: {current_version}
* Last Version: {last_version}
* Manager: {manager}
* Time: {time}
* Status: {status}
* Annotate: {annotate}
* URL: {url}
"""


def render_deployment_desc(description):
    try:
        data = json.loads(description)
    except ValueError:
        data = {}
    ver = data.get('ver')
    if ver and int(ver) == 1:
        return DEPLOYMENT_DESCRIPTION_V1.format(**data)
    return description


MONITOR_DESCRIPTION_V1 = """
* Status: {status}
* Time: {timestamp}
"""


def render_monitor_desc(description):
    try:
        data = json.loads(description)
    except ValueError:
        data = {}
    ver = data.get('ver')
    if ver and int(ver) == 1:
        return MONITOR_DESCRIPTION_V1.format(**data)
    return description
