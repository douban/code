# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.models.tag import TagName


class TagsUI(object):
    _q_exports = []

    def __init__(self, target):
        self.target = target

    def __call__(self, request):
        return self._q_index(request)

    def _q_index(self, request):
        raise TraversalError

    def _q_lookup(self, request, part):
        # TODO: check no '/' in tag name
        name = part
        target_type = self.target.tag_type
        target_id = self.target.id
        tag = TagName.get_by_name_and_target_id(name, target_type, target_id)
        if tag:
            return TagUI(self.target, tag)
        raise TraversalError


class TagUI(object):
    _q_exports = []

    def __init__(self, target, tag):
        self.target = target
        self.tag = tag

    def __call__(self, request):
        return self._q_index(request)

    def _q_index(self, request):
        if request.method == 'POST':
            tag = self.tag
            name = request.get_form_var('name')
            # TODO: check name
            if name and tag.name != name:
                tag.update_name(name)
            color = request.get_form_var('color')
            # color: #xxxxxx
            # TODO: check color
            if color and tag.hex_color != color[1:]:
                tag.update_color(color[1:])
        return request.redirect(self.target.url + 'issues')

    def _q_lookup(self, request, part):
        raise TraversalError
