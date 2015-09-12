# coding: utf-8
from datetime import date, timedelta

from vilya.libs.store import store, bdb, cache
from vilya.models.ticket import TicketComment

MAX_SHOW_CONTRIBUTION_DAYS = 180
MAX_UPDATE_CONTRIBUTION_DAYS = 90


class UserContributions(object):
    KEY_USER_DATE_CONTRIB = "contrib/%s/u_%s"

    @classmethod
    @cache('code:contrib:user:{username}:{days}', expire=60 * 30)
    def get_by_user(cls, username, days=None):
        if days is None:
            days = MAX_SHOW_CONTRIBUTION_DAYS
        c = {}
        for d in xrange(0, int(days)):
            this_day = date.today() - timedelta(days=d)
            user_contribution_by_this_day = cls.get_by_date(
                username, this_day)
            c.setdefault(this_day.strftime("%Y-%m-%d"),
                         (cls.get_score_by_user_contribution(
                             user_contribution_by_this_day),
                          user_contribution_by_this_day))
        return c

    @classmethod
    def update_by_user(cls, username):
        c = {}
        for d in xrange(0, MAX_UPDATE_CONTRIBUTION_DAYS):
            this_day = date.today() - timedelta(days=d)
            user_contribution_by_this_day = cls.update_by_date(
                username, this_day)
            c.setdefault(this_day.strftime("%Y-%m-%d"),
                         (cls.get_score_by_user_contribution(
                             user_contribution_by_this_day),
                          user_contribution_by_this_day))
        return c

    @classmethod
    def get_score_by_user_contribution(cls, contribution_per_day):
        return 100 * len(contribution_per_day['owned_tickets']) + 5 * len(
            contribution_per_day['commented_tickets'])

    @classmethod
    def update_by_date(cls, username, given_date, limit=500, start=0):

        commented_tickets = cls.get_commented_ticket_ids_in_others_merged_PR_by_date(  # noqa
            username, given_date, limit=limit, start=start)

        result = {
            "owned_tickets": cls._get_author_merged_PR_ids_by_date(
                username, given_date, limit=limit, start=start),
            "commented_tickets": commented_tickets,
        }

        bdb.set(cls.KEY_USER_DATE_CONTRIB % (
                given_date.strftime("%Y-%m-%d"), username), result)

        return result

    @classmethod
    def get_by_date(cls, username, given_date, limit=500, start=0):

        cached_result = bdb.get(cls.KEY_USER_DATE_CONTRIB % (
            given_date.strftime("%Y-%m-%d"), username))
        if cached_result:
            return cached_result

        return {"owned_tickets": [],
                "commented_tickets": []}

    @classmethod
    def _get_author_merged_PR_ids_by_date(cls, username, given_date,
                                          limit=500, start=0):
        res = store.execute("select id from codedouban_ticket where "
                            "author=%s and closed is not NULL "
                            "and DATE(time)=%s "
                            "order by time desc limit %s, %s",
                            (username,
                             given_date.strftime("%Y-%m-%d"),
                             start, limit)
                            )
        return [r[0] for r in res]

    @classmethod
    def _iter_others_merged_PR_ids_by_date(cls, username, given_date,
                                           limit=500, start=0):
        res = store.execute("select id from codedouban_ticket where "
                            "author<>%s and closed is not NULL "
                            "and DATE(time)=%s "
                            "order by time desc limit %s, %s",
                            (username,
                             given_date.strftime("%Y-%m-%d"),
                             start, limit)
                            )

        for r in res:
            yield r[0]

    @classmethod
    def get_commented_ticket_ids_in_others_merged_PR_by_date(
            cls, username, given_date, limit=500, start=0):

        others_merged_PR_ids = cls._iter_others_merged_PR_ids_by_date(
            username, given_date, limit=limit, start=start)

        ticket_comment_list = ((tid, TicketComment.gets_by_ticketid(
            tid)) for tid in others_merged_PR_ids)

        get_authors_comments = lambda comments: [
            c for c in comments if c.author == username]

        ticket_ids_and_commented_count = ((tid, len(get_authors_comments(
            comments))) for tid, comments in ticket_comment_list)

        user_commented_ticket_ids_and_commented_count = [
            (tid, cnt)
            for tid, cnt in ticket_ids_and_commented_count if cnt > 0]

        return user_commented_ticket_ids_and_commented_count
