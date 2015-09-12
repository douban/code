# -*- coding: utf-8 -*-

migrate_type_name = {
    'code_review': 'pull_comment',
    # 'commit': 'pull_commit',
}


# 迁移数据
def migrate_notif_data(data, receiver):
    from vilya.models.notification import Notification
    from vilya.models.actions.commit_comment import migrate_commit_comment
    from vilya.models.actions.issue import migrate_issue
    from vilya.models.actions.issue_comment import migrate_issue_comment
    from vilya.models.actions.pull import migrate_pull_request
    from vilya.models.actions.pull_comment import migrate_pull_comment
    from vilya.models.actions.recommend import migrate_recommend
    from vilya.models.actions.team_add_member import migrate_team_add_member

    type_migrate_dict = {
        'commit_comment': migrate_commit_comment,
        'issue': migrate_issue,
        'issue_comment': migrate_issue_comment,
        'pull_request': migrate_pull_request,
        'pull_comment': migrate_pull_comment,
        # 'pull_commit': migrate_pull_commit,
        'recommend': migrate_recommend,
        'team_add_member': migrate_team_add_member,
    }

    assert data.get('uid') is not None
    assert data.get('type') is not None
    uid = data['uid']
    action_type = data['type']

    if action_type in migrate_type_name:
        Notification.set_data(receiver, 'type', migrate_type_name[action_type],
                              uid)
        action_type = migrate_type_name[action_type]

    migrate_data = type_migrate_dict[action_type]
    for new, old in migrate_data.iteritems():
        if data.get(new) is None:
            assert type(old) in (str, tuple, list)
            value = data[old] if isinstance(old, str) else old[1](data.get(old[0]))  # noqa
            Notification.set_data(receiver, new, value, uid)
            data[new] = value
        elif type(old) is list:  # force update
            value = data[old] if isinstance(old, str) else old[1](data.get(old[0]))  # noqa
            Notification.set_data(receiver, new, value, uid)
            data[new] = value

    data['notif_template'] = action_type + '_notif'
    data['feed_template'] = action_type + '_feed'

    return data
