# -*- coding: utf-8 -*-

import json
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


class IssueBase(object):

    def __init__(self, request, target, issue, number, template):
        self.request = request
        self.target = target
        self.issue = issue
        self.issue_id = issue.issue_id
        self.issue_number = number
        self.issue_template = template


class IssueView(IssueBase):

    def index(self):
        from vilya.models.team import Team
        request = self.request
        issue = self.issue
        target = self.target
        issue_template = self.issue_template

        show_close = True
        user = request.user
        current_user = request.user
        author = issue.creator
        i_am_author = user and issue.creator_id == user.username
        i_am_admin = user and target.is_admin(user.name)
        has_user_voted = issue.has_user_voted(user.name) if user else False
        vote_count = issue.vote_count
        teams = Team.get_all_team_uids()
        return HttpResponse(st(issue_template, **locals()))


    def upvote(self):
        issue = self.issue
        request = self.request

        def upvote_action(issue, user, request):
            msg = ''
            count = None
            action = 0
            if not user:
                msg = "You should login before voting on any issue!"
            elif issue.is_closed:
                msg = "You can not vote or unvote a closed issue!"
            elif issue.creator_id == user.name:
                msg = "You can not vote on issues created by yourself!"
            elif request.method == 'PUT':
                count = issue.upvote_by_user(user.name)
                action = 1
            elif request.method == 'DELETE':
                count = issue.cancel_upvote_by_user(user.name)
                action = -1
            else:
                action = 0
                msg = 'Unsupport Method'

            if count is None:
                count = issue.vote_count

            return HttpResponse(json.dumps({
                'action': action,
                'count': count,
                'msg': msg,
            }))
        user = request.user
        return upvote_action(issue, user, request)

    def comment(self):
        from dispatches import dispatch
        from vilya.libs.signals import issue_signal, issue_comment_signal
        from vilya.models.team import Team
        request = self.request
        issue = self.issue
        issue_id = self.issue_id
        target = self.target

        if request.method == 'POST':
            content = request.POST.get('content', '').decode('utf-8')
            user = request.user
            user = user.name if user else None
            if user:
                author = user
                if content.strip():
                    comment = issue.add_comment(content, user)
                    issue.add_participant(user)
                    html = st('/widgets/issue/issue_comment.html', **locals())
                else:
                    return HttpResponse(json.dumps({'error': 'Content is empty'}))

                if request.POST.get('comment_and_close'):
                    issue.close(author)
                    # TODO: 重构feed后取消信号发送
                    issue_signal.send(author=author,
                                      content=content,
                                      issue_id=issue_id)
                    dispatch('issue', data={
                                'sender': author,
                                'content': content,
                                'issue': issue,
                                })
                    return HttpResponse(json.dumps(dict(r=0, reload=1, redirect_to=issue.url)))
                elif request.POST.get('comment_and_open'):
                    issue.open()
                    # TODO: 重构feed后取消信号发送
                    issue_signal.send(author=author, content=content,
                                        issue_id=issue_id)
                    dispatch('issue', data={
                                'sender': author,
                                'content': content,
                                'issue': issue,
                                })
                    return HttpResponse(json.dumps(dict(r=0, reload=1, redirect_to=issue.url)))
                elif content:
                    issue_comment_signal.send(author=author,
                                                content=comment.content,
                                                issue_id=comment.issue_id,
                                                comment_id=comment.id)
                    dispatch('issue_comment', data={
                                'sender': author,
                                'content': comment.content,
                                'issue': issue,
                                'comment': comment})
                participants = issue.participants

                teams = Team.get_all_team_uids()

                participants_html = st('/widgets/participation.html',
                                        **locals())  # FIXME: locals()?
                return HttpResponse(json.dumps(dict(
                    r=0, html=html, participants_html=participants_html)))
        return HttpResponseRedirect(issue.url)

    def tag(self):
        request = self.request
        issue = self.issue
        target = self.target

        def split_tags_str(tags):
            if not tags:
                return []
            tags = tags.split()
            return tags

        if request.method == 'POST':
            user = request.user
            user = user.name if user else None
            if user:
                tags = request.POST.getlist('tags', [])
                if isinstance(tags, basestring):
                    tags = split_tags_str(tags.decode('utf8'))
                tags_orig = [tag.name for tag in issue.tags]
                tags_to_add = list(set(tags).difference(tags_orig))
                tags_to_del = list(set(tags_orig).difference(tags))
                issue.add_tags(tags_to_add, target.id, user)
                issue.remove_tags(tags_to_del, target.id)
        return HttpResponseRedirect(issue.url)

    def milestone(self):
        request = self.request
        issue = self.issue

        if request.method == 'POST':
            user = request.user
            if not user:
                return HttpResponseRedirect(issue.url)
            milestone = request.POST.get('milestone', '')
            milestone_title = request.POST.get('milestone_title', '')
            if milestone == 'new' and milestone_title:
                issue.add_milestone(user, name=milestone_title)
            elif milestone == 'clear':
                issue.remove_milestone()
            else:
                issue.add_milestone(user, milestone_id=milestone)
        return HttpResponseRedirect(issue.url)

    def join(self):
        from vilya.models.team import Team
        request = self.request
        issue = self.issue
        target = self.target  # noqa for template

        user = request.user
        if user:
            issue.add_participant(user.name)
            participants = issue.participants
            teams = Team.get_all_team_uids()
            participants_html = st('/widgets/participation.html',
                                    participants=participants, teams=teams)
            return HttpResponse(json.dumps(dict(r=0, participants_html=participants_html)))
        return HttpResponse(json.dumps(dict(r=1)))

    def leave(self):
        from vilya.models.team import Team
        request = self.request
        issue = self.issue

        user = request.user
        if user:
            if user.name == issue.creator_id:
                return HttpResponse(json.dumps(dict(r=1, msg="Can't leave the issue created by you.")))
            issue.delete_participant(user.name)
            participants = issue.participants
            teams = Team.get_all_team_uids()
            participants_html = st('/widgets/participation.html',
                                    participants=participants, teams=teams)
            return HttpResponse(json.dumps(dict(r=0, participants_html=participants_html)))
        return HttpResponse(json.dumps(dict(r=1)))

    def assign(self):
        request = self.request
        issue = self.issue

        if request.method == 'POST':
            user = request.user
            if user:
                assignee = request.POST.get('assignee', '').decode('utf-8')
                issue.assign(assignee)
        return HttpResponseRedirect(issue.url)
