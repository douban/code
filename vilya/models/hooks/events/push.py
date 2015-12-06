# -*- coding: utf-8 -*-

EMPTY_OID = '0' * 40


class PushEvent(object):
    type = 'push'

    def __init__(self, push):
        self.push = push

    @property
    def payload(self):
        return self.push.payload

"""
payload: {
    "ref":"refs/heads/master",
    "after":"617942d86be4f9040d8b2576cd9a32c853b62d24",
    "before":"8e4b9a330c89019943a67de88db3bef8ff24dbc3",
    "created":false,
    "deleted":false,
    "forced":false,
    "compare":"https://github.com/xtao/test/compare/8e4b9a330c89...617942d86be4",  # noqa
    "commits":[{
        "id":"617942d86be4f9040d8b2576cd9a32c853b62d24",
        "distinct":true,
        "message":"Add",
        "timestamp":"2013-11-20T05:18:28-08:00",
        "url":"https://github.com/xtao/test/commit/617942d86be4f9040d8b2576cd9a32c853b62d24",  # noqa
        "author":{
            "name":"XTao",
            "email":"xutao881001@gmail.com",
            "username":"xtao"},
        "committer":{
            "name":"XTao",
            "email":"xutao881001@gmail.com",
            "username":"xtao"},
        "added":["hook.md"],
        "removed":[],
        "modified":[]}],
    "head_commit":{
        "id":"617942d86be4f9040d8b2576cd9a32c853b62d24",
        "distinct":true,
        "message":"Add",
        "timestamp":"2013-11-20T05:18:28-08:00",
        "url":"https://github.com/xtao/test/commit/617942d86be4f9040d8b2576cd9a32c853b62d24",  # noqa
        "author":{
            "name":"XTao",
            "email":"xutao881001@gmail.com",
            "username":"xtao"},
        "committer":{
            "name":"XTao",
            "email":"xutao881001@gmail.com",
            "username":"xtao"},
        "added":["hook.md"],
        "removed":[],
        "modified":[]},
    "repository":{
        "id":13925321,
        "name":"test",
        "url":"https://github.com/xtao/test",
        "description":"Test~",
        "watchers":0,
        "stargazers":0,
        "forks":0,
        "fork":false,
        "size":136,
        "owner":{
            "name":"xtao",
            "email":"xutao881001@gmail.com"},
        "private":false,
        "open_issues":1,
        "has_issues":true,
        "has_downloads":true,
        "has_wiki":true,
        "created_at":1382963502,
        "pushed_at":1384953548,
        "master_branch":"master"},
    "pusher":{
        "name":"xtao",
        "email":"xutao881001@gmail.com"}
}
"""


class PushPayload(object):
    """<old-value> SP <new-value> SP <ref-name> LF"""

    def __init__(self, project, old_value, new_vaule, ref_name, user_name):
        self.old_value = old_value
        self.new_vaule = new_vaule
        self.ref_name = ref_name
        self.project = project
        self.user_name = user_name

    @property
    def before(self):
        return self.old_value

    @property
    def after(self):
        return self.new_vaule

    @property
    def ref(self):
        return self.ref_name

    @property
    def repository(self):
        repo = dict(url=self.project.repo_url,
                    name=self.project.name,
                    description=self.project.description,
                    owner=dict(name=self.project.owner_name))
        return repo

    @property
    def commits(self):
        repo = self.project.repo
        if not repo:
            return []
        if repo.empty:
            return []
        if any(EMPTY_OID == _ for _ in (self.after, self.before)):
            return []
        _commits = repo.get_commits(self.after, self.before)
        commits = [dict(id=commit.sha,
                        author=dict(name=commit.author_name,
                                    email=commit.author_email),
                        url=commit.url,
                        message=commit.message,
                        # FIXME: date format
                        timestamp=commit.author_time.strftime(
                            "%Y-%m-%dT%H:%M:%S %z")
                        ) for commit in _commits]
        return commits

    @property
    def payload(self):
        payload = dict(before=self.before,
                       after=self.after,
                       ref=self.ref,
                       repository=self.repository,
                       commits=self.commits,
                       user_name=self.user_name,
                       type="push")
        return payload
