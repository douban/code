#!/usr/bin/env python
# coding: utf-8

from vilya.models.mute import Mute
from vilya.views.api.utils import jsonize
from quixote.errors import RequestError

_q_exports = []

ALLOWED_MUTE_TYPE = ['ticket', ]


def _q_lookup(request, type_):
    user = request.user
    if (type_ in ALLOWED_MUTE_TYPE) and user:
        return MuteUI(type_)
    else:
        return RequestError('Can not parse your request')


class MuteUI(object):
    _q_exports = []

    def __init__(self, type_):
        self._type = type_
        self.parts = []

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def _q_index(self, request):
        if self._type == 'ticket':
            if len(self.parts) >= 2:
                proj_name = '/'.join(self.parts[:-1])
                target_id = self.parts[-1]
                if proj_name and target_id.isdigit():
                    self._proj_name = proj_name
                    self._target_id = target_id
                    self._user = request.user
                    self._cancel = request.get_form_var("cancel")
                    return self.mute()
        return RequestError("Invalie args!")

    @jsonize
    def mute(self):
        if self._cancel:
            Mute.unmute(self._type, self._proj_name, self._target_id,
                        self._user)
            return {"status": 'on'}
        else:
            Mute.mute(self._type, self._proj_name, self._target_id,
                      self._user)
            return {"status": 'off'}
