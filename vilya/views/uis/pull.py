# -*- coding: utf-8 -*-

from __future__ import absolute_import
from itertools import groupby
from quixote.errors import TraversalError, AccessError

from vilya.libs.template import st
from vilya.libs.text import get_mentions_from_text
from dispatches import dispatch
from vilya.views.util import jsonize
from vilya.models.user import User
from vilya.models.elastic import SearchEngine
from vilya.models.elastic.issue_pr_search import PullRequestSearch
from vilya.models.project import CodeDoubanProject
from vilya.models.pull import PullRequest, add_pull, merge_pull, close_pull
from vilya.models.commit_statuses import CommitStatuses
from vilya.models.ticket import Ticket
from vilya.models.linecomment import PullLineComment
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY
from vilya.models.team import Team

TICKETS_COUNT_PER_PAGE = 30


class TicketUI(object):
    _q_exports = ['comment', 'commits', 'files', 'review_comment',
                  'check_merge', 'merge', 'edit', 'discussion_tab',
                  'commits_tab', 'files_tab']

    def __init__(self, proj_name, ticket_id):
        self.proj_name = proj_name
        self.ticket_id = ticket_id
        self.project = CodeDoubanProject.get_by_name(proj_name)
        self.ticket = Ticket.get_by_projectid_and_ticketnumber(
            self.project.id, self.ticket_id)
        self.pullreq = PullRequest.get_by_proj_and_ticket(
            self.project.id, self.ticket_id)
        try:
            self.all_commits = self.pullreq.commits
        except Exception:
            self.all_commits = self.pullreq.get_merged_commits()

    def _add_additional_commits(self):
        # FIXME: Used in views/api/__init__.py
        delta_commits = self.pullreq.get_delta_commits()
        if delta_commits:
            value = ','.join(c.sha for c in delta_commits)
            author = self.pullreq.from_proj.owner_name
            if self.ticket.add_commits(value, author):
                # 补充commits则发送通知邮件给pr参与者
                dispatch('new_commits',
                         data={
                             'pullreq': self.pullreq,
                             'ticket': self.ticket,
                             'deltacommits': delta_commits,
                         })

    def _q_index(self, request):
        return self._render(request)

    @property
    def url(self):
        return str('/%s/pull/%s/' % (self.proj_name, self.ticket_id))

    def commits(self, request):
        return self._render(request, 'commits')

    def files(self, request):
        return self._render(request, 'files')

    def _render(self, request, view='', error=None):
        current_user = request.user
        # TODO: user flash message
        ticket = self.ticket
        pullreq = self.pullreq
        project = self.project
        commits = self.all_commits
        try:
            diff_length = pullreq.get_diff_length()
        except:
            # FIXME: more exception detail
            diff_length = 0
        user = request.user
        has_proj_perm = project.has_push_perm(user.name) if user else False
        show_merge_guide = (has_proj_perm or user.username == ticket.author) \
            if user and not ticket.closed else False
        if not pullreq.merged and not ticket.closed:
            # FIXME: 这使得发邮件的时机有点奇怪？没人请求页面就不发吗？
            delta_commits = self.pullreq.get_delta_commits()
            if delta_commits:
                value = ','.join(c.sha for c in delta_commits)
                author = self.pullreq.from_proj.owner_name
                if self.ticket.add_commits(value, author):
                    # 补充commits则发送通知邮件给pr参与者
                    dispatch('new_commits',
                             data={
                                 'pullreq': self.pullreq,
                                 'ticket': self.ticket,
                                 'deltacommits': delta_commits,
                             })
        return st('/pull/ticket.html', **locals())

    def discussion_tab(self, request):
        # TODO: 把 get_diff 提到这里做
        user = request.user
        current_user = request.user
        ticket = self.ticket
        pullreq = self.pullreq
        project = self.project
        has_proj_perm = project.has_push_perm(user.name) if user else False
        show_merge_guide = (
            has_proj_perm or user.username == ticket.author) \
            if user and not ticket.closed else False
        show_close = has_proj_perm or user.name == ticket.author \
            if user and not ticket.closed else False
        show_reopen = has_proj_perm or user.name == ticket.author \
            if user and ticket.closed and not pullreq.merged \
            and not pullreq.is_temp_pull() else False

        # 可以@到team_id
        teams = Team.get_all_team_uids()

        codereviews_group = ticket.get_codereviews_group()
        # 根据 patch(paths, from_sha) 缓存 raw_diff
        raw_diff_by_patch = {}
        key_func = lambda x: x.old_path + x.from_sha
        diff_by_linecomment_id = {}
        for id, linecomments in codereviews_group.iteritems():
            _default = linecomments[0]
            if key_func(_default) in raw_diff_by_patch:
                _diff = pullreq.get_diff(
                    raw_diff=raw_diff_by_patch[key_func(_default)],
                    linecomments=linecomments)
            else:
                _diff = pullreq.get_diff(
                    ref=_default.from_sha, paths=_default.paths,
                    rename_detection=True, linecomments=linecomments)
                if _diff:
                    raw_diff_by_patch[key_func(_default)] = _diff.raw_diff
            diff_by_linecomment_id[_default.id] = _diff

        return st('/pull/ticket_thread.html', **locals())

    def commits_tab(self, request):
        user = request.user
        ticket = self.ticket
        pullreq = self.pullreq
        project = self.project
        commits = self.all_commits
        has_proj_perm = project.has_push_perm(user.name) if user else False
        show_merge_guide = (
            has_proj_perm or user.username == ticket.author) \
            if user and not ticket.closed else False
        return st('/pull/commits_pane.html', **locals())

    def files_tab(self, request):
        # call by ajax
        user = request.user
        current_user = request.user
        ticket = self.ticket
        pullreq = self.pullreq
        project = self.project
        has_proj_perm = project.has_push_perm(user.name) if user else False
        show_merge_guide = (
            has_proj_perm or user.username == ticket.author) \
            if user and not ticket.closed else False

        # get line comments

        # commits = self.all_commits
        # last_commit_ref = commits[0].sha if commits else ''
        # linecomments = PullLineComment.gets_by_target_and_ref(
        #    self.ticket.id, last_commit_ref)
        linecomments = PullLineComment.gets_by_target(self.ticket.id)

        # get diff(patches)
        # FIXME: ignore_space，这是被ajax请求的，js那边没这逻辑。应该在前端加一个按钮
        whitespace = request.get_form_var('w', '0')
        if whitespace.isdigit() and int(whitespace) == 1:
            ignore = True
        else:
            ignore = False
        try:
            diff = pullreq.get_diff(ignore_space=ignore, rename_detection=True,
                                    linecomments=linecomments)
        except:
            # FIXME: diff 的默认值不该为 []，其他很多地方也是
            diff = []

        return st('/pull/diffs_pane.html', **locals())

    @jsonize
    def comment(self, request):
        if request.method == 'POST':
            content = request.get_form_var('content').decode('utf-8')
            if not content.strip():
                return {'error': 'Content is empty!'}
            user = request.user
            current_user = request.user
            author = user.name
            comment = self.ticket.add_comment(content, author)
            ticket = self.ticket
            pullreq = self.pullreq
            project = self.project
            html = st('/pull/ticket_comment.html', **locals())

            if request.get_form_var('comment_and_close'):

                close_pull(ticket, pullreq, user, content, comment, request)

                return dict(r=0, reload=1, redirect_to=self.url)
            elif request.get_form_var('comment_and_reopen'):
                if not pullreq.is_temp_pull():
                    ticket.open(author)
                return dict(r=0, reload=1, redirect_to=self.url)
            else:
                at_users = get_mentions_from_text(content)
                for u in at_users:
                    User(u).add_invited_pull_request(ticket.id)
            return dict(r=0, html=html)
        return request.redirect(self.url)

    # TODO: 增加前端信息后修改
    @jsonize
    def review_comment(self, request):
        ''' pull linecomment '''
        user = request.user
        current_user = request.user
        if request.method == 'POST' and user:
            project = CodeDoubanProject.get_by_name(self.proj_name)
            project_id = project.id
            from_sha = request.get_form_var('from_sha')
            assert from_sha, "comment from_sha cannot be empty"
            old_path = request.get_form_var('old_path')
            assert old_path, "comment old_path cannot be empty"
            new_path = request.get_form_var('new_path')
            # position = request.get_form_var('position')
            # assert position, "comment position cannot be empty"
            from_oid = request.get_form_var('from_oid')
            assert from_oid, "comment from_oid cannot be empty"
            to_oid = request.get_form_var('to_oid')
            assert to_oid, "comment to_oid cannot be empty"
            old = request.get_form_var('old_no')
            old = int(old) if old.isdigit() else LINECOMMENT_INDEX_EMPTY
            new = request.get_form_var('new_no')
            new = int(new) if new.isdigit() else LINECOMMENT_INDEX_EMPTY
            content = request.get_form_var('content', '').decode('utf-8')
            # commit_author = request.get_form_var('commit_author')
            if not content.strip():
                return {'error': 'Content is empty!'}
            author = user.name
            ticket = self.ticket
            linecomment = ticket.add_codereview(from_sha, '',
                                                old_path, new_path, from_oid,
                                                to_oid, old, new,
                                                author, content)
            pullreq = self.pullreq
            codereviews = [linecomment]

            at_users = get_mentions_from_text(content)
            for u in at_users:
                User(u).add_invited_pull_request(ticket.id)

            # TODO: 把dispatch 从model移到这里

            # r.html_with_diff used by codelive
            return dict(
                r=0,
                html=st('/pull/ticket_linecomment.html', **locals()),
                html_with_diff=st('/pull/render_ticket_codereview.html',
                                  **locals()))

    def check_merge(self, request):
        """ return merge guide widget """
        ticket = self.ticket
        project = self.project
        pullreq = self.pullreq
        auto_mergable = self.pullreq.is_auto_mergable()
        can_fastforward = self.pullreq.can_fastforward()
        user = request.user

        # FIXME menghan: 如果latest_commit_status不是针对最后一个commit，那么结果有误导性
        latest_commit_status = None
        commits = pullreq.commits
        for commit in commits:
            cs = CommitStatuses(pullreq.from_proj.id, commit.sha)
            latest_commit_status = cs.latest()
            if latest_commit_status:
                break

        has_perm = project.has_push_perm(user.name) if user else False
        show_merge_btn = has_perm and not pullreq.is_up_to_date()
        return st('/pull/merge_guide.html',
                  auto_mergable=auto_mergable,
                  can_fastforward=can_fastforward,
                  latest_commit_status=latest_commit_status,
                  show_merge_btn=show_merge_btn,
                  project=project,
                  pullreq=pullreq,
                  user=user,
                  ticket=ticket,
                  )

    # TODO: return json?
    # FIXME: pass 'error'
    def merge(self, request):
        if request.method == 'GET':
            return request.redirect(str('/%s/pull/%s/' % (
                self.proj_name, self.ticket_id)))

        user = request.user
        commit_message = request.get_form_var(
            'commit_message', '').decode('utf-8')
        if user:
            error = merge_pull(self.ticket, self.pullreq, user,
                               commit_message, request)
            if error:
                return self._render(request, error=error)

        return request.redirect(str('/%s/pull/%s/' % (
            self.proj_name, self.ticket_id)))

    def edit(self, request):
        if request.method == 'POST':
            title = request.get_form_var('title', '').decode('utf-8')
            content = request.get_form_var('content', '').decode('utf-8')
            user = request.user
            user = user.name if user else None
            if user == self.ticket.author:
                self.ticket.update(title, content)
        return request.redirect(self.url)


class PullUI(object):

    _q_exports = ['new', 'create', 'commit_preview']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(proj_name)

    def _q_lookup(self, request, pullid):
        if request.get_path().find('newpull') > 0:
            return request.redirect(request.get_path().replace(
                'newpull', 'pull'))
        if pullid.count('.') == 1:
            pullid, diff_type = pullid.split('.')
            pr = PullRequest.get_by_proj_and_ticket(self.project.id, pullid)
            resp = request.response
            resp.set_header("Content-Type", "text/plain")
            if diff_type == 'patch' and pr:
                text = pr.get_format_patch()
                return text.encode('utf-8')
            elif diff_type == 'diff' and pr:
                text = pr.get_diff_tree()
                return text
            else:
                raise TraversalError

        if pullid.isdigit():
            ticket = Ticket.get_by_projectid_and_ticketnumber(
                self.project.id, pullid)
            if ticket:
                return TicketUI(self.proj_name, pullid)
        raise TraversalError

    def new(self, request):
        user = request.user
        if not user:
            raise AccessError
        from_proj = self.project
        from_ref = request.get_form_var('head_ref', from_proj.default_branch)
        parent_proj = from_proj.get_forked_from()
        to_proj = request.get_form_var('base_repo')
        if to_proj:
            to_proj = CodeDoubanProject.get_by_name(to_proj)
        elif parent_proj:
            to_proj = parent_proj
        else:
            to_proj = from_proj
        if not to_proj:
            raise TraversalError("The PR's upstream project is not existed")
        to_ref = request.get_form_var('base_ref', to_proj.default_branch)
        if from_proj != to_proj:
            # Allow to create PR to a different project only if user has push perm
            # ~~A bit weird, maybe should be separate perms
            # ~~If from and to projects are the same, we should be in online edit mode
            if not from_proj.has_push_perm(user.name):
                raise AccessError(
                    "Need push permission to add a PR on another project")
        pullreq = PullRequest.open(from_proj, from_ref, to_proj, to_ref)
        family = from_proj.get_fork_network()
        from_branches = from_proj.repo.branches
        to_branches = to_proj.repo.branches
        from_commit = pullreq.from_commit
        to_commit = pullreq.to_commit
        if not pullreq.can_pull:
            raise TraversalError(
                "The PR's head_ref or base_ref is not existed")
        highlighted_projects = filter(None, [from_proj, parent_proj])
        commits = pullreq.commits
        n_commits = len(commits)
        n_authors = len(set(c.author.username for c in commits))
        ticket_title, ticket_desc = self._choose_default_PR_title_and_description(commits)  # noqa

        # get diff
        diff = pullreq.get_diff(rename_detection=True)
        n_files = diff.length

        grouped_commits = groupby(commits, lambda c: c.author_time.date())

        prs = PullRequest.get_by_from_and_to(
            from_proj.id, from_ref, to_proj.id, to_ref)
        open_pullreqs = []
        for pr in prs:
            t = Ticket.get_by_projectid_and_ticketnumber(
                to_proj.id, pr.ticket_id)
            if t and t.closed is None:
                open_pullreqs.append(pr)
        guideline_url = get_project_guidelines(to_proj)
        teams = Team.get_all_team_uids()
        return st('/pull/new.html', **locals())

    def _choose_default_PR_title_and_description(self, commits):
        commits = [c for c in commits
                   if not c.shortlog.startswith('Merge branch')]
        if len(commits) == 1:
            commit = commits[0]
            ticket_title = commit.shortlog
            ticket_desc = commit.message.partition('\n')[-1].strip()
        else:
            ticket_title = ticket_desc = ''
        return ticket_title, ticket_desc

    @property
    def commit_preview(self):
        return CommitPreviewUI(self.project)

    def create(self, request):
        user = request.user
        if not user:
            raise AccessError
        from_proj = request.get_form_var('from_proj')
        from_ref = request.get_form_var('from_ref')
        to_ref = request.get_form_var('to_ref')
        to_proj = request.get_form_var('to_proj')
        title = request.get_form_var('title', '').decode('utf-8')
        comment = request.get_form_var('body', '').decode('utf-8')
        if not all([from_ref, from_proj, to_ref, to_proj]):
            raise TraversalError
        from_proj = CodeDoubanProject.get_by_name(from_proj)
        to_proj = CodeDoubanProject.get_by_name(to_proj)
        if from_proj != to_proj:
            if not from_proj.has_push_perm(user.name):
                raise AccessError(
                    "Need push permission to create PR on another project")

        pullreq = PullRequest.open(from_proj, from_ref, to_proj, to_ref)
        ticket = Ticket(None, None, to_proj.id, title, comment,
                        user.username, None, None)
        pullreq = add_pull(ticket, pullreq, user)
        ticket = pullreq.ticket
        return request.redirect(str('/%s/pull/%s/' % (to_proj.name,
                                                      ticket.ticket_id)))


class CommitPreviewUI(object):
    # FIXME: ajax接口，统一返回json {r=0/1, html=...}

    """ for commit preview widget,
        currently used by pull/new and compare chooser """
    _q_exports = []

    def __init__(self, project, path=''):
        self.project = project
        self.path = path

    def _q_lookup(self, request, name):
        if ':' not in name:
            return CommitPreviewUI(self.project, name)
        if self.path:
            name = '/'.join((self.path, name))
        projname, ref = name.split(':')
        project = CodeDoubanProject.get_by_name(projname)
        if not project:
            raise TraversalError
        repo = project.repo
        ref = ref and repo.sha(ref)
        if not ref:
            raise TraversalError
        commit = repo.get_commit(ref)
        return st('widgets/commit_preview.html', **locals())


class PullsUI(object):

    _q_exports = ['closed', 'all_data', 'search']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(proj_name)
        if not self.project:
            raise TraversalError()

    def get_tickets(self, project, page, closed=False):
        tickets = Ticket.gets_by_proj(
            project.id, closed=closed, limit=TICKETS_COUNT_PER_PAGE,
            start=TICKETS_COUNT_PER_PAGE * (int(page) - 1))
        if closed:
            tickets = sorted(tickets, key=lambda x: x.closed, reverse=True)
        ticket_total_len = Ticket.get_count_by_proj(project.id, closed=closed)
        return tickets, ticket_total_len

    def _q_index(self, request):
        return self._index(request)

    def _index(self, request):
        key_word = request.get_form_var('q')
        user = request.user
        project = self.project
        page = request.get_form_var('page', 1)
        tickets, ticket_total_len = self.get_tickets(project, page)
        n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
        is_closed_tab = False
        open_tab_link = self.open_tab_link
        close_tab_link = self.close_tab_link
        return st('/pull/pulls.html', **locals())

    def search(self, request):
        key_word = request.get_form_var('q')
        if not key_word:
            return self._index(request)
        status = request.get_form_var('status')
        user = request.user
        page = request.get_form_var('page', 1)
        project = self.project
        tickets = []
        ticket_len = Ticket.get_count_by_proj_id(project.id)
        search_result = PullRequestSearch.search_a_phrase(
            key_word, project.id, size=ticket_len)
        if search_result and not search_result.get('error'):
            ticket_ids = [id for id, in SearchEngine.decode(
                search_result, ['ticket_id'])]
            tickets = Ticket.gets_by_projectid_and_ticketnumbers(
                project.id, ticket_ids)
            if status == "closed":
                tickets = [t for t in tickets if t.closed]
            else:
                tickets = [t for t in tickets if not t.closed]
        ticket_total_len = len(tickets)
        limit = TICKETS_COUNT_PER_PAGE
        start = TICKETS_COUNT_PER_PAGE * (int(page) - 1)
        tickets = tickets[start:start + limit]
        n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
        if status == "closed":
            is_closed_tab = True
        else:
            is_closed_tab = False
        open_tab_link = self.open_tab_link
        close_tab_link = self.close_tab_link
        return st('/pull/pulls.html', **locals())

    def closed(self, request):
        key_word = request.get_form_var('q')
        user = request.user
        project = self.project
        page = request.get_form_var('page', 1)
        tickets, ticket_total_len = self.get_tickets(
            project, page, closed=True)
        n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
        is_closed_tab = True
        open_tab_link = self.open_tab_link
        close_tab_link = self.close_tab_link
        return st('/pull/pulls.html', **locals())

    @property
    def open_tab_link(self):
        return '/%s/pulls/' % self.project.name

    @property
    def close_tab_link(self):
        return '/%s/pulls/closed' % self.project.name

    @jsonize
    def all_data(self, request):
        tickets = Ticket.gets_all_by_proj(self.project.id)
        return [dict(id=str(t.ticket_number), title=t.title,
                     content=t.description) for t in tickets]

    def _q_lookup(self, request, alias):
        if User.check_exist(alias):
            return PullsByAuthorUI(self.proj_name, alias)
        raise TraversalError


class PullsByAuthorUI(PullsUI):
    _q_exports = ['closed']

    def __init__(self, proj_name, alias):
        super(PullsByAuthorUI, self).__init__(proj_name)
        self.alias = alias

    def get_tickets(self, project, page, closed=False):
        tickets = Ticket.gets_by_proj_and_author(
            project.id, self.alias, closed=closed,
            limit=TICKETS_COUNT_PER_PAGE,
            start=TICKETS_COUNT_PER_PAGE * (int(page) - 1))
        if closed:
            tickets = sorted(tickets, key=lambda x: x.closed, reverse=True)
        ticket_total_len = Ticket.get_count_by_proj_and_author(
            project.id, self.alias, closed=closed)
        return tickets, ticket_total_len

    @property
    def open_tab_link(self):
        return '/%s/pulls/%s/' % (self.project.name, self.alias)

    @property
    def close_tab_link(self):
        return '/%s/pulls/%s/closed' % (self.project.name, self.alias)

    def _q_lookup(self, request, name):
        raise TraversalError


class TeamPullsUI(object):

    _q_exports = ['closed']

    def __init__(self, team_name):
        self.team_name = team_name
        self.team = Team.get_by_uid(team_name)

    def _q_index(self, request):
        user = request.user
        team = self.team
        page = request.get_form_var('page', 1)
        tickets = Ticket.gets_by_team_id(
            team.id, limit=TICKETS_COUNT_PER_PAGE,
            start=TICKETS_COUNT_PER_PAGE * (int(page) - 1)) or []
        ticket_total_len = Ticket.get_count_by_team_id(team.id) or 0
        is_closed_tab = False
        n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
        return st('/teams/team_pulls.html', **locals())

    def closed(self, request):
        user = request.user
        team = self.team
        page = request.get_form_var('page', 1)
        tickets = Ticket.gets_by_team_id(
            team.id, closed=True, limit=TICKETS_COUNT_PER_PAGE,
            start=TICKETS_COUNT_PER_PAGE * (int(page) - 1)) or []
        ticket_total_len = Ticket.get_count_by_team_id(team.id,
                                                       closed=True) or 0
        n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
        is_closed_tab = True
        return st('/teams/team_pulls.html', **locals())


def get_project_guidelines(project):
    ref = project.repo.default_branch
    for t in ('md', 'rst', 'txt'):
        guideline_file = 'CONTRIBUTING.{}'.format(t)
        content = project.repo.get_file_by_ref('%s:%s' % (ref, guideline_file))
        if content is None:
            continue
        if content.startswith('http'):
            # 引用了外部的Contributing Guidelines 地址
            return content.strip()
        else:
            return project.full_url + '/blob/{0}/{1}'.format(
                ref, guideline_file)
    return None
