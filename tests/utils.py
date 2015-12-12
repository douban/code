import os
import tempfile
import shutil

from mock import Mock
from contextlib import contextmanager

from vilya.libs import gyt
from vilya.libs.permdir import get_repo_root
from ellen.repo import Jagare
from vilya.models.project import CodeDoubanProject


TEMP_PROJECT_OWNER = 'testuser'
TEMP_PROJECT_DESCRIPTION = 'This is a test project.'
BARE_REPO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'bare_repo1')

content_a = """a_hunk = [('idem', u'/* highlight style */'), ('rem', u'.highlight { color: #008000; font-weight: bold; } /* Keyword */'), ('add', u'.highlight .hll { background-color: #ffffcc; }'), ('add', u'.highlight  { background: #ffffff; }'), ('add', u'.highlight .c { color: #808080; } /* Comment */'), ('add', u'.highlight .err { color: #F00000; background-color: #F0A0A0; } /* Error */'), ('add', u'.highlight .k { color: #008000; font-weight: bold; } /* Keyword */'), ('idem', u'.highlight .o { color: #303030; } /* Operator */'), ('idem', u'.highlight .cm { color: #808080; } /* Comment.Multiline */'), ('idem', u'.highlight .cp { color: #507090; } /* Comment.Preproc */')]"""  # noqa
content_b = """a_hunk = [('idem', u'/* highlight style */'), ('rem', u'.highlight { color: #008000; font-weight: bold; } /* Keyword */'), ('add', u'.highlight .hll { background-color: #ffffcc; }'), ('add', u'.highlight  { backggggground: #ffffff; }'), ('add', u'.high .c { color: #808080; } /* Coomment */'), ('add', u'.highlight .err { color: #F00000; background-color: #F00A0A0; } /* Error */'), ('add', u'.highlight .k { color: #008000; font-weight: bold; } /* Keyword */'), ('idem', u'.highlight .o { color: #303; } /* Operator ****/'), ('idem', u'.highlight .cm { color: #808080; } /* Comment.Multiline */'),('idem', u'adfadsfadsf'),  ('idem', u'.highlight .cp { color: #507090; } /* Comment.Preproc */')]"""  # noqa


@contextmanager
def mkdtemp():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@contextmanager
def chdir(dir):
    cwd = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(cwd)


class FakeEnv(object):
    """A fake trac env"""

    def __init__(self, name):
        self.project_name = name


@contextmanager
def new_git_bare_repo():
    with mkdtemp() as tmpdir:
        gyt.call(['git', 'init', '--bare', tmpdir])
        yield tmpdir


@contextmanager
def clone(git_dir):
    with mkdtemp() as work_path:
        gyt.call(['git', 'clone', git_dir, work_path])
        assert os.path.exists(work_path + '/.git')
        yield work_path

        with chdir(work_path):
            gyt.call(['git', 'config', 'user.name', 'test author'])
            gyt.call(['git', 'config', 'user.email', 'ta@example.com'])
            gyt.call(['git', 'add', "."])
            gyt.call(['git', 'commit', '-m', 'test'], _raise=True)
            gyt.call(['git', 'push', 'origin', 'master'], _raise=True)


def mock_method(real_method):
    mock = Mock(wraps=real_method)

    def _(*a, **kw):
        return mock(*a, **kw)
    _.mock = mock
    return _


def setup_repos(tmpdir, prj_name='test_proj'):
    delete_project(prj_name)
    origin_project = CodeDoubanProject.add(prj_name, 1,
                                           create_trac=False)
    path = origin_project.git_real_path
    with clone(path) as workdir:
        with open(os.path.join(workdir, 'origin'), 'w') as f:
            f.write(content_a)
    delete_project(prj_name + '_fork')
    fork_project = CodeDoubanProject.add(prj_name + '_fork', 2,
                                         fork_from=origin_project.id,
                                         create_trac=False)
    fork_path = fork_project.git_real_path
    repo = origin_project
    fork_repo = fork_project
    return path, repo, fork_path, fork_repo


@contextmanager
def setup2repos(prj_name):
    """setup_2_repos_and_make_changes_in_fork"""
    with mkdtemp() as tmpdir:
        path, repo, fork_path, fork_repo = setup_repos(tmpdir, prj_name)

        with clone(fork_path) as work_path:
            with open(os.path.join(work_path, 'a'), 'w') as f:
                f.write(content_b)

        yield path, repo, fork_path, fork_repo


def get_temp_project(origin=None, repo_path=BARE_REPO_PATH):
    if origin:
        prefix_path = get_repo_root()
        temp_repo_path = tempfile.mkdtemp(suffix=".git",
                                          prefix="test_",
                                          dir=prefix_path)
        project_name = temp_repo_path[len(prefix_path) + 1:][:-4]
        project = CodeDoubanProject.add(project_name,
                                        TEMP_PROJECT_OWNER,
                                        TEMP_PROJECT_DESCRIPTION,
                                        fork_from=origin.id,
                                        create_trac=False)
        return project

    prefix_path = get_repo_root()
    temp_repo_path = tempfile.mkdtemp(suffix=".git",
                                      prefix="test_",
                                      dir=prefix_path)
    project_name = temp_repo_path[len(prefix_path) + 1:][:-4]
    project = CodeDoubanProject.add(project_name, TEMP_PROJECT_OWNER,
                                    TEMP_PROJECT_DESCRIPTION)

    shutil.rmtree(temp_repo_path)
    repo = Jagare(repo_path)
    repo.clone(temp_repo_path, bare=True)

    return project


def delete_project(names):
    if isinstance(names, basestring):
        names = [names]
    for n in names:
        prj = CodeDoubanProject.get_by_name(n)
        if prj:
            prj.delete()
