# -*- coding: utf-8 -*-
from random import shuffle

from vilya.libs.template import st
from vilya.models.consts import MY_PULL_REQUESTS_TAB_INFO

_q_exports = []


def _q_index(request):
    user = request.user
    if user:
        list_type = request.get_form_var("list_type", "invited")

        n_invited = user.n_open_invited
        n_participated = user.n_open_participated
        n_yours = user.n_user_open_submit_pull_requests
        counts = [n_invited, n_participated, n_yours, None]
        tab_info = []
        for tab, count in zip(MY_PULL_REQUESTS_TAB_INFO, counts):
            tab.update(count=count)
            tab_info.append(tab)

        if list_type == "participated":
            tickets = user.get_participated_pull_requests()
        elif list_type == "yours":
            tickets = user.get_user_submit_pull_requests()
        elif list_type == "explore":
            from vilya.models.ticket import Ticket
            tickets = Ticket.gets_all_opened()
            ticket_total_len = len(tickets)
            shuffle(tickets)
        else:
            tickets = user.get_invited_pull_requests()
        is_closed_tab = False
        ticket_total_len = len(tickets)
        return st('my_pull_requests.html', **locals())
