# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.libs.template import st

from vilya.models.project import CodeDoubanProject
from vilya.models.board import CodeDoubanBoard, CodeDoubanTicketBoard
from vilya.views.hub.pytrello import TrelloClient

_q_exports = []


class BoardUI:
    _q_exports = ['setting']

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def _q_index(self, request):
        project_name = self.proj_name
        project = CodeDoubanProject.get_by_name(project_name)
        if not project:
            raise TraversalError()

        if project.board and project.board.board_id:
            client = TrelloClient(
                project.board.user_key, project.board.user_token)
            _board = client.get_board(project.board.board_id)
            if not _board:
                return request.redirect('/%s/board/setting' % project_name)
            member_avatars = _board.member_avatars()
            lists = _board.open_lists()
            cards = _board.open_cards()
            card_data = {}
            for lst in lists:
                card_data[lst] = [
                    card for card in cards if card.list_id == lst.id]
        else:
            return request.redirect('/%s/board/setting' % project_name)

        return st('board.html', **locals())

    def setting(self, request):
        project_name = self.proj_name
        project = CodeDoubanProject.get_by_name(project_name)
        if not project:
            raise TraversalError()
        if request.method == 'POST':
            project_id = project.id
            user_key = request.get_form_var('user_key')
            user_token = request.get_form_var('user_token')
            board_index = request.get_form_var('board_index')
            board_id = request.get_form_var('board_id%s' % board_index)
            board_name = request.get_form_var('board_name%s' % board_index)
            CodeDoubanBoard.add(
                project_id, board_id, board_name, user_key, user_token)

            return request.redirect('/%s/board' % project_name)

        return st('board_setting.html', **locals())


class TicketBoardUI:
    _q_exports = []

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def _q_index(self, request):
        project_name = self.proj_name
        project = CodeDoubanProject.get_by_name(project_name)
        if not project:
            raise TraversalError()
        tickets = CodeDoubanTicketBoard(
            self.proj_name).tickets_group_by_status()
        return st('ticket_board.html', **locals())


def get_ticket_link(project_name, desc):
    import re
    for r in re.compile(r'#\d+', re.DOTALL).findall(desc):
        desc = desc.replace(
            r, '<a target="_blank" href="/%s/ticket/%s">%s</a>' % (project_name, r[1:], r))   # noqa
    return desc
