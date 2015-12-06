from blinker import Namespace

_signals = Namespace()
recommend_signal = _signals.signal('recommend_signal')
comment_signal = _signals.signal('comment_signal')
codereview_signal = _signals.signal('code_review')
pullrequest_signal = _signals.signal('pullrequest')
push_signal = _signals.signal('push_signal')
follow_user_signal = _signals.signal('follow_user_signal')

# Issue
issue_signal = _signals.signal('issue')
issue_comment_signal = _signals.signal('issue_comment')

# Team
team_created_signal = _signals.signal('team_created')
team_joined_signal = _signals.signal('team_joined')
team_add_member_signal = _signals.signal('team_add_member')

# Repository
repo_create_signal = _signals.signal('repo_create')
repo_watch_signal = _signals.signal('repo_watch')
repo_fork_signal = _signals.signal('repo_fork')

# Gist
gist_created_signal = _signals.signal('gist_created')
gist_commented_signal = _signals.signal('gist_commented')
gist_starred_signal = _signals.signal('gist_starred')
gist_forked_signal = _signals.signal('gist_forked')
gist_updated_signal = _signals.signal('gist_updated')

# redis publish
rds_pub_signal = _signals.signal('rds_pub')
