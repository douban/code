"""vilya URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.views.generic.base import RedirectView
from views.django import views
from views.django import user
from views.django import team
from views.django import team_issue
from views.django import gist
from views.django import gist_user
from views.django import gist_raw
from views.django import gist_embed
from views.django import gist_comment
from views.django import badge
from views.django import project
from views.django import project_setting
from views.django import project_issue
from views.django import trello
from views.django import setting
from views.django import hub
from views.django import hub_team


urlpatterns = [
    # user
    url(r'^login/?$', user.login, name='user_login'),
    url(r'^logout/?$', user.logout, name='user_logout'),
    url(r'^register/?$', user.register, name='user_register'),
    url(r'^people/(?P<username>\w+)/praises', user.praises, name='user_praises'),
    url(r'^people/(?P<username>\w+)/followers', user.followers, name='user_followers'),
    url(r'^people/(?P<username>\w+)/following', user.following, name='user_following'),
    url(r'^people/(?P<username>\w+)/badges', user.badges, name='user_badges'),
    url(r'^people/(?P<username>\w+)/contributions', user.contributions, name='user_contributions'),
    url(r'^people/(?P<username>\w+)/contribution_detail', user.contribution_detail, name='user_contribution_detail'),
    url(r'^people/(?P<username>\w+)', user.index, name='user_index'),
    url(r'^watching/?$', user.watching, name="user_watching"),
    url(r'^favorites/?$', user.favorites, name="user_favorites"),
    url(r'^praise/?$', user.praise_index, name="user_praise_index"),
    url(r'^praise/vote/?$', user.praise_vote, name="user_praise_vote"),
    url(r'^trello/bind/?$', trello.bind, name="trello_bind"),
    url(r'^trello/unbind/?$', trello.unbind, name="trello_unbind"),
    url(r'^settings/?$', setting.index, name='setting_index'),
    url(r'^settings/emails$', RedirectView.as_view(pattern_name='setting_emails')),
    url(r'^settings/emails/$', setting.emails, name='setting_emails'),
    url(r'^settings/emails/(?P<id>[0-9]+)/delete/?$', setting.emails_delete, name='setting_emails_delete'),
    url(r'^settings/emails/(?P<id>[0-9]+)/set_notif/?$', setting.emails_set_notif, name='setting_emails_set_notif'),
    url(r'^settings/emails/(?P<id>[0-9]+)/un_notif/?$', setting.emails_un_notif, name='setting_emails_un_notif'),
    url(r'^settings/github$', RedirectView.as_view(pattern_name='setting_github')),
    url(r'^settings/github/$', setting.github, name='setting_github'),
    url(r'^settings/github/(?P<id>[0-9]+)/?$', setting.github_delete, name='setting_github_delete'),
    url(r'^settings/notification$', RedirectView.as_view(pattern_name='setting_notification')),
    url(r'^settings/notification/$', setting.notification, name='setting_notification'),
    url(r'^settings/notification/setting/?$', setting.notification_setting, name='setting_notification_setting'),
    url(r'^settings/ssh$', RedirectView.as_view(pattern_name='setting_ssh')),
    url(r'^settings/ssh/$', setting.ssh, name='setting_ssh'),
    url(r'^settings/ssh/(?P<id>[0-9]+)/?$', setting.ssh_delete, name='setting_ssh_delete'),
    url(r'^settings/codereview$', RedirectView.as_view(pattern_name='setting_codereview')),
    url(r'^settings/codereview/$', setting.codereview, name='setting_codereview'),
    url(r'^settings/codereview/setting/?$', setting.codereview_setting, name='setting_codereview_setting'),
    url(r'^hub/beacon/?$', hub.beacon, {'path': ''}),
    url(r'^hub/beacon/(?P<path>.*)$', hub.beacon, name='hub_beacon'),
    url(r'^hub/stat/?$', hub.stat_index, name='hub_stat_index'),
    url(r'^hub/stat/source/?$', hub.stat_source, name='hub_stat_source'),
    url(r'^hub/emoji/?$', hub.emoji, name='hub_emoji'),
    url(r'^hub/public_timeline/?$', hub.public_timeline, name='hub_public_timeline'),
    url(r'^hub/yours/?$', hub.yours, name='hub_yours'),
    url(r'^hub/search/?$', hub.search, name='hub_search'),
    url(r'^hub/create/?$', hub.create, name='hub_create'),
    url(r'^hub/future/?$', hub.future, name='hub_future'),
    url(r'^hub/add_team/?$', hub.add_team, name='hub_add_team'),
    url(r'^hub/my_issues/?$', hub.my_issues),
    url(r'^hub/my_issues/repos/?$', hub.my_issues, name='hub_my_issues'),
    url(r'^hub/my_issues/assigned/?$', hub.my_issues_assigned, name='hub_my_issues_assigned'),
    url(r'^hub/my_issues/created_by/?$', hub.my_issues_created_by, name='hub_my_issues_created_by'),
    url(r'^hub/my_issues/participated/?$', hub.my_issues_participated, name='hub_my_issues_participated'),
    url(r'^hub/my_pull_requests/?$', hub.my_pull_requests, name='hub_my_pull_requests'),

    # team
    url(r'^teams/?$', team.teams, name="team_teams"),
    url(r'^teams/(?P<name>\w+)/?$', hub_team.team_index, name="hub_team_team_index"),
    url(r'^teams/(?P<name>\w+)/pulls/?$', hub_team.team_pulls, name="hub_team_team_pulls"),
    url(r'^teams/(?P<name>\w+)/pulls/closed/?$', hub_team.team_pulls_closed, name="hub_team_team_pulls_closed"),
    url(r'^teams/(?P<name>\w+)/issues/?$', hub_team.team_issues, name="hub_team_team_issues"),
    url(r'^teams/(?P<name>\w+)/issues/repos/?$', hub_team.team_issues, name="hub_team_team_issues"),
    url(r'^teams/(?P<name>\w+)/issues/assigned/?$', hub_team.team_issues, name="hub_team_team_issues"),
    url(r'^teams/(?P<name>\w+)/issues/created_by/?$', hub_team.team_issues, name="hub_team_team_issues"),
    url(r'^teams/(?P<name>\w+)/issues/new/?$', hub_team.team_issues_new, name="hub_team_team_issues_new"),
    url(r'^teams/(?P<name>\w+)/issues/create/?$', hub_team.team_issues_create, name="hub_team_team_issues_create"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/?$', team_issue.issue, name="team_issue_issue"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/upvote/?$', team_issue.issue_upvote, name="team_issue_issue_upvote"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/comment/?$', team_issue.issue_comment, name="team_issue_issue_comment"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/tag/?$', team_issue.issue_tag, name="team_issue_issue_tag"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/join/?$', team_issue.issue_join, name="team_issue_issue_join"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/leave/?$', team_issue.issue_leave, name="team_issue_issue_leave"),
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/assign/?$', team_issue.issue_assign, name="team_issue_issue_assign"),
    # FIXME(xutao) team milestone is working?
    url(r'^teams/(?P<name>\w+)/issues/(?P<id>[0-9]+)/milestone/?$', team_issue.issue_milestone, name="team_issue_issue_milestone"),
    url(r'^teams/(?P<name>\w+)/issue_comments/(?P<id>[0-9]+)/edit/?$', team_issue.comment_edit, name="team_issue_comment_edit"),
    url(r'^teams/(?P<name>\w+)/issue_comments/(?P<id>[0-9]+)/delete/?$', team_issue.comment_delete, name="team_issue_comment_delete"),

    # project
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/blob/(?P<revision>\w+)/(?P<path>.*)$', project.ProjectBlobView.as_view(), name="project_blob"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/edit/(?P<revision>\w+)/(?P<path>.*)$', project.ProjectEditView.as_view(), name="project_edit"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/blame/(?P<revision>\w+)/(?P<path>.*)$', project.ProjectBlameView.as_view(), name="project_blame"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/raw/(?P<revision>\w+)/(?P<path>.*)$', project.ProjectRawView.as_view(), name="project_raw"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/commits/(?P<revision>\w+)/(?P<path>.*)$', project.ProjectCommitsView.as_view(), name="project_commits"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/tree/(?P<revision>[\w\-]+)/(?P<path>.*)$', project.ProjectTreeView.as_view(), name="project_tree"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/browsefiles/?$', project.browsefiles, name="project_browsefiles"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/code_review/(?P<id>[0-9]+)/delete/?$', project.codereview_delete, name="project_codereview_delete"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/code_review/(?P<id>[0-9]+)/edit/?$', project.codereview_edit, name="project_codereview_edit"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/comments/?$', project.comment, name="project_comment"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/comments/new/?$', project.comment_new, name="project_comment_new"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/comments/(?P<id>[0-9]+)/?$', project.comment_delete, name="project_comment_delete"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/compare/?$', project.compare_index, name="project_compare_index"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/compare/(?P<range>.*)$', project.compare_range, name="project_compare_range"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/?$', project_issue.issues_index, name="project_issues"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/new/?$', project_issue.issues_new, name="project_issues_new"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/create/?$', project_issue.issues_create, name="project_issues_create"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/assigned/?$', project_issue.issues_assigned, name="project_issues_assigned"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/search/?$', project_issue.issues_search, name="project_issues_search"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/created_by/?$', project_issue.issues_created_by, name="project_issues_created_by"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/mentioned/?$', project_issue.issues_metioned, name="project_issues_mentioned"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/tags/(?P<name>[\w:]+)/?$', project_issue.issues_tags_tag, name="project_issues_tags_tag"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/?$', project_issue.issue, name="project_issue_index"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/upvote/?$', project_issue.issue_upvote, name="project_issue_upvote"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/assign/?$', project_issue.issue_assign, name="project_issue_assign"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/leave/?$', project_issue.issue_leave, name="project_issue_leave"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/join/?$', project_issue.issue_join, name="project_issue_join"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/tag/?$', project_issue.issue_tag, name="project_issue_tag"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/milestone/?$', project_issue.issue_milestone, name="project_issue_milestone"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issues/(?P<id>[0-9]+)/comment/?$', project_issue.issue_comment, name="project_issue_comment"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issue_comments/(?P<id>[0-9]+)/edit/?$', project_issue.issue_comments_comment_edit, name="project_issue_comments_comment_edit"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/issue_comments/(?P<id>[0-9]+)/delete/?$', project_issue.issue_comments_comment_delete, name="project_issue_comments_comment_delete"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/watchers/?$', project.watchers, name="project_watchers"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/forkers/?$', project.forkers, name="project_forkers"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/archive/(?P<revision>\w+)/?$', project.archive, name="project_archive"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/?$', project_setting.index, name="project_setting_index"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/add_committer/?$', project_setting.add_committer, name="project_setting_add_committer"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/del_committer/?$', project_setting.del_committer, name="project_setting_del_committer"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/sphinx_docs/?$', project_setting.sphinx_docs, name="project_setting_sphinx_docs"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/hooks/?$', project_setting.hooks_index, name="project_setting_hooks_index"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/hooks/new/?$', project_setting.hooks_new, name="project_setting_hooks_new"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/hooks/(?P<id>[0-9]+)/?$', project_setting.hooks_hook, name="project_setting_hooks_hook"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/conf/?$', project_setting.conf, name="project_setting_conf"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/pages/?$', project_setting.pages, name="project_setting_pages"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/transfer_project/?$', project_setting.transfer_project, name="project_setting_transfer_project"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/rename_project/?$', project_setting.rename_project, name="project_setting_rename_project"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/groups/?$', project_setting.groups_index, name="project_setting_groups_index"),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/settings/groups/destroy/?$', project_setting.groups_destory, name="project_setting_groups_destroy"),
    # FIXME(xutao) move `^watch/?$` to user
    url(r'^watch/?$', project.watch_index, name="project_watch_index"),
    url(r'^watch/(?P<id>[0-9]+)/?$', project.watch, name="project_watch"),
    url(r'^fetch/(?P<id>[0-9]+)/?$', project.fetch, name="project_fetch"),

    # gist
    url(r'^gist/$', gist.index, name='gist_index'),
    url(r'^gist/discover$', gist.discover, name='gist_discover'),
    url(r'^gist/forked$', gist.forked, name='gist_forked'),
    url(r'^gist/starred$', gist.starred, name='gist_starred'),
    url(r'^gist/(?P<username>\w+)/forked$', gist_user.forked, name='gist_user_forked'),
    url(r'^gist/(?P<username>\w+)/starred$', gist_user.starred, name='gist_user_starred'),
    url(r'^gist/(?P<username>\w+)/?$', gist_user.index, name='gist_user_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/?$', gist_user.gist_index, name='gist_gist_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+).js$', gist_embed.index, name='gist_embed_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/comments/$', gist_comment.index, name='gist_comment_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/comments/(?P<comment_id>[0-9]+)$', gist_comment.comment, name='gist_comment_comment'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/revisions/$', gist_user.gist_revisions, name='gist_user_gist_revisions'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/download$', gist_user.gist_download, name='gist_user_gist_download'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/edit$', gist_user.gist_edit, name='gist_user_gist_edit'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/delete$', gist_user.gist_delete, name='gist_user_gist_delete'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/(?P<revision>\w+)$', gist_user.gist_index, name='gist_gist_index_revision'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/raw/(?P<revision>\w+)/(?P<filename>.*)$', gist_raw.index, name='gist_raw_index'),

    # badge
    url(r'^badge/?$', badge.timeline),
    url(r'^badge/fetch_new/?$', badge.fetch_new, name='badge_fetch_new'),
    url(r'^badge/all/?$', badge.all, name='badge_all'),
    url(r'^badge/timeline/?$', badge.timeline, name='badge_timeline'),
    url(r'^badge/badges/?$', badge.badges, name='badge_badges'),
    url(r'^badge/items/?$', badge.items, name='badge_items'),
    url(r'^badge/count/?$', badge.count, name='badge_count'),
    url(r'^badge/add/?$', badge.add, name='badge_add'),
    url(r'^badge/(?P<id>[0-9]+)/?$', badge.badge_index, name='badge_badge_index'),
    url(r'^badge/(?P<id>[0-9]+)/people/?$', badge.badge_people, name='badge_badge_people'),

    # misc
    url(r'^mirrors/?$', views.mirrors, name="views_mirrors"),
    url(r'^j/fav/?$', views.j_fav, name="views_j_fav"),
    url(r'^j/pull/(?P<id>[0-9]+)/?$', views.j_pull_edit, name="views_j_pull_edit"),
    # TODO(xutao) move '^j/issue/(?P<id>[0-9]+)/edit/?$' to issue or api
    url(r'^j/issue/(?P<id>[0-9]+)/edit/?$', views.j_issue_edit, name="views_j_issue_edit"),
    url(r'^j/issue/delete_tag/?$', views.j_issue_delete_tag, name="views_j_issue_delete_tag"),
    url(r'^j/hooks/(?P<id>[0-9]+)/telchar/?$', views.j_hooks_telchar, name="views_j_hooks_telchar"),
    url(r'^j/chat/delete_room/?$', views.j_chat_delete_room, name="views_j_chat_delete_room"),
    url(r'^j/chat/(?P<name>\w+)/?$', views.j_chat_room, name="views_j_chat_room"),
    url(r'^j/more/notify/(?P<id>[0-9]+)/?$', views.j_more_notify, name="views_j_more_notify"),
    url(r'^j/more/team/(?P<name>\w+)/(?P<number>[0-9]+)/?$', views.j_more_team, name="views_j_more_team"),
    url(r'^j/more/userfeed/(?P<id>[0-9]+)/?$', views.j_more_userfeed, name="views_j_more_userfeed"),
    url(r'^j/more/pub/(?P<id>[0-9]+)/?$', views.j_more_pub, name="views_j_more_pub"),
    url(r'^m/?$', views.m_index, name="views_m_index"),
    url(r'^m/public_timeline/?$', views.m_public_timeline, name="views_m_public_timeline"),
    url(r'^m/actions/?$', views.m_actions, name="views_m_actions"),
    url(r'^admin/', admin.site.urls),

    # Match last
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)$', RedirectView.as_view(pattern_name='project_index')),
    url(r'^(?P<username>\w+)/(?P<projectname>\w+)/$', project.ProjectTreeView.as_view(), {'revision': '', 'path': ''}, name="project_index"),
]
