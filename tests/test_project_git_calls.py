# -*- coding: utf-8 -*-

import os

from vilya.models.project import CodeDoubanProject
from vilya.libs import gyt
from vilya.libs.permdir import get_repo_root

from tests.base import TestCase
from tests.utils import delete_project

T_MSG1 = u'msg1呀'
T_AUTHOR = u'Test Author 不是我'
T_AUTHOR_EMAIL = 'test@example.com'
T_AUTHOR2 = u'Test Author 是我'
T_AUTHOR_EMAIL2 = 'test2@example.com'
T_FILE1 = u'是file1'


class TestProjectGitCalls(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def tearDown(self):
        TestCase.tearDown(self)

    def _path_for_clone(self, name):
        return os.path.join(get_repo_root(), '%s.clone' % name)

    def _commit_push(self, proj, objs, msg='testmsg', author=T_AUTHOR,
                     author_email=T_AUTHOR_EMAIL):
        repo = gyt.repo(proj.git.path)
        clone_path = self._path_for_clone(proj.name)
        if os.path.exists(clone_path):
            clone = gyt.repo(clone_path, bare=False)
        else:
            clone = repo.clone(clone_path, bare=False)
        # TODO allow commiting more than one file
        # assert os.path.exists(repo.work_tree), \
        # noqa "repo.work_tree must exist, check if repo has been created with bare=False"
        for filename, content in objs:
            f = open(os.path.join(clone.work_tree, filename), 'w')
            f.write(content)
            f.close()
            clone.call(['add', filename])
        clone.call(['commit', '--author', '%s <%s>' % (
            author, author_email), '-m', msg], _env=self.env_for_git)
        clone.call('push origin HEAD')
        return clone.sha()

    def _proj(self, name='test_proj', owner='test_user'):
        delete_project(name)
        proj = CodeDoubanProject.add(name, owner, create_trac=False)
        return proj

    def test_commit_encoded_chinese(self):
        content = 'content1串串'
        proj = self._proj('prj')
        sha = self._commit_push(proj, [[T_FILE1, content]], T_MSG1)
        assert sha

    def test_add(self):
        proj = self._proj('prj')
        assert proj.name == 'prj'
        assert gyt.is_git_dir(proj.git.path)

    def test_fork(self):
        proj = self._proj('test_proj')
        fork = proj.fork('test_proj_fork', 'user2')
        assert gyt.is_git_dir(fork.git.path)
        assert fork.fork_from == proj.id
        assert fork.id != proj.id

    def test_get_src(self):
        proj = self._proj('test_get_src')
        self._commit_push(proj, [[T_FILE1, 'content1']], T_MSG1)
        src = proj.git.get_src(T_FILE1)
        assert src == ('blob', 'content1')

    def test_get_src_with_chinese_in_filename(self):
        proj = self._proj('test_get_src')
        filename = u'fn文件'
        self._commit_push(proj, [[filename, 'content1 space']], T_MSG1)
        src = proj.git.get_src()
        assert src[1][0]['path'] == filename

    def test_get_src_with_space_in_filename(self):
        proj = self._proj('test_get_src')
        filename = 'fn space'
        self._commit_push(proj, [[filename, 'content1 space']], T_MSG1)
        src = proj.git.get_src(filename)
        assert src == ('blob', 'content1 space')

    def test_get_src_for_tree_with_space_in_filename(self):
        proj = self._proj('test_get_src')
        filename = u'fn space'
        self._commit_push(proj, [[filename, 'content1 space']], T_MSG1)
        src = proj.git.get_src()
        assert src[0] == 'tree'
        assert src[1][0]['path'] == filename
        assert src[1][0]['name'] == filename
        assert src[1][0]['type'] == 'blob'

    def test_get_src_commited_twice(self):
        proj = self._proj('test_get_src_2')
        self._commit_push(proj, [[T_FILE1, 'content1']], T_MSG1)
        self._commit_push(proj, [[T_FILE1, 'content1 bis']], T_MSG1)
        src = proj.git.get_src(T_FILE1)
        assert src == ('blob', 'content1 bis')

    def test_get_src_file_by_commited(self):
        proj = self._proj('test_get_src_by_commited')
        sha1 = self._commit_push(proj, [[T_FILE1, 'content1']], T_MSG1)
        sha2 = self._commit_push(proj, [[T_FILE1, 'content1 bis']], T_MSG1)
        src = proj.git.get_src(T_FILE1, ref=sha1)
        assert src == ('blob', 'content1')
        src = proj.git.get_src(T_FILE1, ref=sha2)
        assert src == ('blob', 'content1 bis')

    def test_get_src_tree_by_commited(self):
        proj = self._proj('test_get_src_by_commited')
        sha1 = self._commit_push(proj, [['f1', 'c1'], ['f2', 'c2']], T_MSG1)
        sha2 = self._commit_push(proj, [['f1', 'c1bis'], ['f3', 'c3']], 'msg2')
        typ, tree = proj.git.get_src('', ref=sha1)
        assert typ == 'tree'
        assert len(tree) == 2
        t = tree[0]
        assert 'id' in t
        assert t['path'] == 'f1'
        assert t['name'] == 'f1'
        assert t['type'] == 'blob'
        assert t['mode'] == '100644'
        # second commit
        typ, tree = proj.git.get_src('', ref=sha2)
        assert typ == 'tree'
        assert len(tree) == 3
        assert set(t['name'] for t in tree) == set(['f1', 'f2', 'f3'])

    def test_latest_update_timestamp(self):
        proj = self._proj('test_latest_update_timestamp')
        import datetime as dt
        before = dt.datetime.now() - dt.timedelta(seconds=1)
        self._commit_push(proj, [[T_FILE1, 'content1串串']], T_MSG1)
        self._commit_push(proj, [[T_FILE1, 'content1 bis串串']], T_MSG1)
        after = dt.datetime.now() + dt.timedelta(seconds=1)
        ts = proj.git.get_last_update_timestamp()
        upd_time = dt.datetime.fromtimestamp(ts)
        assert before < upd_time < after

    def test_get_raw_content(self):
        proj = self._proj('test')
        sha = self._commit_push(proj, [[T_FILE1, 'content1串串']], T_MSG1)
        assert proj.git.get_raw_content(T_FILE1) == u'content1串串'
        self._commit_push(proj, [[T_FILE1, 'content1 bis串串']], T_MSG1)
        assert proj.git.get_raw_content(T_FILE1) == u'content1 bis串串'
        assert proj.git.get_raw_content(T_FILE1, sha) == u'content1串串'

    def test_latest_commit(self):
        proj = self._proj('test')
        fn = 'abcd_ef'
        sha = self._commit_push(proj, [[fn, 'cont串串ent1']], T_MSG1)
        assert proj.git.latest_commit(fn) == sha
        sha = self._commit_push(proj, [[fn, 'cont串串ent2']], 'msg2')
        assert proj.git.latest_commit(fn) == sha

    def test_latest_commit_file_with_chinese(self):
        proj = self._proj('test')
        fn = u'abcd ef 儿儿儿 gh'
        sha = self._commit_push(proj, [[fn, 'cont串串ent1']], T_MSG1)
        assert proj.git.latest_commit(fn) == sha
        sha = self._commit_push(proj, [[fn, 'cont串串ent2']], 'msg2')
        assert proj.git.latest_commit(fn) == sha

    def test_get_revisions(self):
        proj = self._proj('test')
        sha1 = self._commit_push(proj, [[T_FILE1, 'cont串串ent1']], T_MSG1)
        sha2 = self._commit_push(proj, [[T_FILE1, 'cont串串ent2']], 'msg2')
        sha3 = self._commit_push(
            proj, [[T_FILE1, 'cont串串ent3']], 'msg3\n\nmsgbody\ncont.')
        revs = proj.git.get_revisions('HEAD~2', 'HEAD')
        assert [(r['id'], r['message']) for r in revs] == [(
            sha3, 'msg3\n    \n    msgbody\n    cont.'), (sha2, 'msg2')]
        revs = proj.git.get_revisions('HEAD~1', 'HEAD')
        assert len(revs) == 1
        assert revs[0]['message'] == 'msg3\n    \n    msgbody\n    cont.'
        assert 'name' in revs[0]
        assert 'date' in revs[0]
        assert 'email' in revs[0]
        revs = proj.git.get_revisions('HEAD', 'HEAD')
        assert revs == []

    def test_blame_src(self):
        proj = self._proj('test')
        sha1 = self._commit_push(
            proj, [[T_FILE1, 'line1\nline2\nline3\nline4串串']], T_MSG1)
        sha2 = self._commit_push(
            proj, [[T_FILE1, 'line1\nline2 CHANGED\nline3\nline4串串']],
            'msg2')
        header, blames = proj.git.blame_src('HEAD', T_FILE1)
        assert header['parents'] == sha1
        assert len(blames) == 4
        assert blames[1][0] == sha2
        assert blames[1][2] == 'test@example.com'
        assert blames[1][4] == 'msg2'
        assert blames[1][6] == '2'
        assert blames[1][10] == 'line2 CHANGED'
        assert blames[0][0] == sha1
        assert blames[0][2] == 'test@example.com'
        assert blames[0][4] == T_MSG1
        assert blames[0][6] == '1'
        assert blames[0][10] == 'line1'

    def test_get_commits(self):
        # BE CAREFUL, Do not work with Chinese in filenames
        proj = self._proj('test')
        commit_sha1 = self._commit_push(proj, [['file1', 'aaaa']], T_MSG1)
        commit_sha2 = self._commit_push(proj, [['file2', 'bbbb']], 'msg2')
        commit_sha3 = self._commit_push(proj, [['file2', 'bbbb\c']], 'msg3')
        commits = proj.git.get_commits()
        assert len(commits) == 2
        sha1 = proj.git.call('rev-parse HEAD:file1')
        sha2 = proj.git.call('rev-parse HEAD:file2')
        assert set(commits.keys()) == set([sha1, sha2])
        c1 = commits[sha1]
        assert c1['name'] == 'file1'
        assert c1['path'] == 'file1'
        assert c1['message'] == T_MSG1
        assert c1['hash'] == commit_sha1
        assert c1['type'] == 'blob'
        assert c1['mode'] == '100644'
        assert c1['contributor'] == 'test'
        assert c1['contributor_url'] == False
        assert c1['id'] == sha1
        c2 = commits[sha2]
        assert c2['hash'] == commit_sha3

    def test_get_revlist(self):
        proj = self._proj('test')
        msg = "msg_title1\n\nmsgbody"
        sha1 = self._commit_push(proj, [[T_FILE1, 'aaaa串串']], msg)
        rl = proj.git.get_revlist()
        assert len(rl) == 1
        assert rl[0]['parents'] == ''
        assert rl[0]['commit'] == sha1
        assert rl[0]['message'] == 'msg_title1'  # Only the message tiltle
        sha2 = self._commit_push(proj, [[T_FILE1, 'bbbb串串']], 'msg2')
        rl = proj.git.get_revlist()
        assert len(rl) == 2
        assert rl[0]['parents'] == [sha1]
        assert rl[0]['commit'] == sha2
        assert rl[0]['message'] == 'msg2'

    def test_get_revlist_by_author(self):
        proj = self._proj('test')
        msg = "msg_title1\n\nmsgbody"
        self._commit_push(proj, [[T_FILE1, 'aaa']], msg,
                          author='a1', author_email='a1@douban.com')
        self._commit_push(proj, [[T_FILE1, 'aab']], msg,
                          author='a2', author_email='a2@douban.com')
        self._commit_push(proj, [[T_FILE1, 'aac']], msg,
                          author='a1', author_email='a1@douban.com')
        rl = proj.git.get_revlist(author='a1@douban.com')
        assert len(rl) == 2

    def test_gitstats(self):
        proj = self._proj('test')
        self._commit_push(proj, [[T_FILE1, 'aaaa串串']], T_MSG1)
        self._commit_push(proj, [['file2', 'bbbb串串']], 'msg2')
        self._commit_push(proj, [[T_FILE1, 'cccc串串']], 'msg32')
        stats = proj.git.get_gitstats_data()
        assert stats.authors[T_AUTHOR]['commits'] == 3
        self._commit_push(proj, [[T_FILE1, 'dddd串串']], 'msg33')
        stats = proj.git.get_gitstats_data()
        assert stats.authors[T_AUTHOR]['commits'] == 4
        self._commit_push(proj, [[T_FILE1, 'eeeee串']], 'msg34')
        stats = proj.git.get_gitstats_data()
        assert stats.authors[T_AUTHOR]['commits'] == 5
        self._commit_push(proj, [[T_FILE1, 'ffff串']], 'msg44',
                          author=T_AUTHOR2, author_email=T_AUTHOR_EMAIL2)
        stats = proj.git.get_gitstats_data()
        assert stats.authors[T_AUTHOR]['commits'] == 5
        assert stats.authors[T_AUTHOR2]['commits'] == 1

    def test_parse_diff(self):
        proj = self._proj('test')
        filename = 'testfile'
        sha1 = self._commit_push(
            proj, [[filename, 'line1\nline2\nline3\nline4串串']], T_MSG1)
        sha2 = self._commit_push(
            proj, [[filename, 'line1\nline2 CHANGED\nline3\nline4串串']],
            'msg2\n\nmsg2 body')
        pd = proj.git.parse_diff()
        assert pd['body'] == 'msg2 body'
        assert pd['author'] == T_AUTHOR
        assert len(pd['difflist']) == 1
        assert pd['parents'] == sha1
        assert pd['time']
        assert pd['message'] == 'msg2'
        assert pd['email'] == T_AUTHOR_EMAIL
        diff = pd['difflist'][0]
        assert diff.old_sha
        assert diff.new_sha
        assert diff.filepath == filename
        assert len(diff.chunks) == 1
        chunk = diff.chunks[0]
        assert chunk.diff_lines == [('idem', u' line1'), ('rem', u'-\x00-line2\x01'), ('add', u'+\x00+line2 CHANGED\x01'), ('idem', u' line3'), ('idem', u' line4\u4e32\u4e32')]  # noqa
        assert chunk.tip_line == u'@@ -1,4 +1,4 @@'

    def test_parse_diff_chinese_filename(self):
        proj = self._proj('test')
        filename = u'test 你好file'
        sha1 = self._commit_push(
            proj, [[filename, 'line1\nline2\nline3\nline4串串']], T_MSG1)
        sha2 = self._commit_push(proj, [[filename, 'line1\nline2 CHANGED\nline3\nline4串串']], 'msg2\n\nmsg2 body')  # noqa
        pd = proj.git.parse_diff()
        diff = pd['difflist'][0]
        assert diff.filepath == filename

    def test_parse_diff_on_first_commit(self):
        proj = self._proj('test')
        filename = 'testfile'
        self._commit_push(
            proj, [[filename, 'line1\nline2\nline3\nline4串串']], T_MSG1)
        pd = proj.git.parse_diff()
        assert pd['body'] == ''
        assert pd['author'] == T_AUTHOR
        assert len(pd['difflist']) == 1
        assert pd['parents'] == ''
        assert pd['time']
        assert pd['message'] == T_MSG1
        assert pd['email'] == T_AUTHOR_EMAIL
        diff = pd['difflist'][0]
        assert diff.new_sha
        assert diff.filepath == filename
        assert len(diff.chunks) == 1
        chunk = diff.chunks[0]
        assert chunk, diff_lines == [('add', u'line1'), ('add', u'line2'), ('add', u'line3'), ('add', u'line4\u4e32\u4e32'), ('other', u' No newline at end of file')]  # noqa
        assert chunk.tip_line == u'@@ -0,0 +1,4 @@'

    def test_parse_diff_with_bad_message(self):
        proj = self._proj('test')
        filename = 'testfile'
        self._commit_push(
            proj, [[filename, 'line1\nline2\nline3\nline4串串']], T_MSG1)
        self._commit_push(proj, [[filename, 'line1\nline2 CHANGED\nline3\nline4串串']], 'msg2\nmsg2 body')  # noqa
        pd = proj.git.parse_diff()
        assert pd['body'] == ''
        assert pd['message'] == 'msg2 msg2 body'
