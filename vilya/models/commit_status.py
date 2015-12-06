# -*- coding: utf-8 -*-

from vilya.libs.props import PropsMixin


# New commit status
class ExtraCommitStatus(PropsMixin):

    def __init__(self, project, id):
        self.id = id
        self.project = project

    def get_uuid(self):
        return '/extra_commit_status/%s:%s' % (self.project.id, self.id)

    def get_extra(self):
        return self.props

    def update_extra(self, **kw):
        props = self.props
        # get_props_item
        # set_props_item
        # delete_props_item
        for key in kw:
            props[key] = kw[key]
        self.props = props
        return props
