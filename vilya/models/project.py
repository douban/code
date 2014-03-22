# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from vilya.config import HOOKS_DIR, DOMAIN
from vilya.libs.permdir import get_repo_root
from vilya.models import ModelField, BaseModel
from vilya.models.git.repo import ProjectRepo

BOARD_ROLES = {'card': 1,
               'archive': 2,
               'issue': 3}


class Project(BaseModel):
    __table__ = "projects"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField(default='')
    owner_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    upstream_id = ModelField(as_key=ModelField.KeyType.DESC)
    family_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)

    def __repr__(self):
        return "<Project,%s,%s>" % (self.id, self.full_name)

    def after_create(self):
        self.init_board()
        self.init_repo()

    def init_repo(self):
        # init repo
        upstream = self.upstream
        if upstream:
            upstream.repo.clone(self.repo_path, bare=True)
            repo = self.repo
        else:
            repo = ProjectRepo.init(self.repo_path)
        repo.update_hooks(HOOKS_DIR)

    def init_board(self):
        # init board
        from vilya.models.board import Board, ProjectBoardCounter
        number = ProjectBoardCounter.incr(project_id=self.id)
        Board.create(name="Issue",
                     position=1,
                     number=number,
                     project_id=self.id,
                     creator_id=self.owner_id,
                     role=BOARD_ROLES['issue'])
        number = ProjectBoardCounter.incr(project_id=self.id)
        Board.create(name="Archive",
                     position=0,
                     number=number,
                     project_id=self.id,
                     creator_id=self.owner_id,
                     role=BOARD_ROLES['archive'])
        number = ProjectBoardCounter.incr(project_id=self.id)
        Board.create(name="To Do",
                     position=2,
                     number=number,
                     project_id=self.id,
                     creator_id=self.owner_id,
                     role=BOARD_ROLES['card'])
        number = ProjectBoardCounter.incr(project_id=self.id)
        Board.create(name="Doing",
                     position=3,
                     number=number,
                     project_id=self.id,
                     creator_id=self.owner_id,
                     role=BOARD_ROLES['card'])
        number = ProjectBoardCounter.incr(project_id=self.id)
        Board.create(name="Done",
                     position=4,
                     number=number,
                     project_id=self.id,
                     creator_id=self.owner_id,
                     role=BOARD_ROLES['card'])

    def rm_repo(self):
        # TODO: move to ellen
        import shutil
        shutil.rmtree(self.repo_path)

    @BaseModel.transaction
    def fork(self, user_id):
        fork = Project.create(name=self.name,
                              description=self.description,
                              kind=self.kind,
                              owner_id=user_id,
                              creator_id=user_id,
                              upstream_id=self.id,
                              family_id=self.family_id)
        return fork

    @property
    def upstream(self):
        return Project.get(id=self.upstream_id)

    @property
    def forks(self):
        return Project.gets(upstream_id=self.id)

    @property
    def families(self):
        return Project.gets(family_id=self.family_id)

    def can_push(self, user):
        if not user:
            return False
        owner = self.owner
        return True if owner.id == user.id else False

    def forked(self, user):
        if self.upstream_id:
            return Project.get(owner_id=user.id, family_id=self.family_id)
        if self.owner_id == user.id:
            return self

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    full_name=self.full_name,
                    description=self.description,
                    owner_name=self.owner_name,
                    owner_id=self.owner_id)

    ## git wrap
    @property
    def clone_url(self):
        return "%s%s.git" % (DOMAIN, self.full_name)

    @property
    def full_name(self):
        owner_name = self.owner_name
        if owner_name:
            return '%s/%s' % (owner_name, self.name)
        return "%s" % self.id

    @property
    def repo_path(self):
        return os.path.join(get_repo_root(), '%s.git' % self.id)

    @property
    def remote_name(self):
        return str(self.id)

    @property
    def owner_name(self):
        return self.owner.name

    @property
    def owner(self):
        from vilya.models.user import User
        from vilya.models.organization import Organization
        owner = User.get(id=self.owner_id)
        return owner

    @property
    def repo(self):
        if not (hasattr(self, '_repo') and self._repo):
            self._repo = ProjectRepo(self)
        return self._repo

    # board wrap
    @property
    def issue_board(self):
        from vilya.models.board import Board
        board = Board.get(project_id=self.id, role=BOARD_ROLES['issue'])
        return board

    @property
    def archive_board(self):
        from vilya.models.board import Board
        board = Board.get(project_id=self.id, role=BOARD_ROLES['archive'])
        return board

    @property
    def card_boards(self):
        from vilya.models.board import Board
        boards = Board.gets(project_id=self.id, role=BOARD_ROLES['card'])
        return boards

    @property
    def boards(self):
        from vilya.models.board import Board
        boards = Board.gets(project_id=self.id)
        return boards

    @BaseModel.transaction
    def create_board(self, **kw):
        from vilya.models.board import Board, ProjectBoardCounter
        number = ProjectBoardCounter.incr(project_id=self.id)
        kw['number'] = number
        kw['project_id'] = self.id
        board = Board.create(**kw)
        return board

    # card wrap
    @BaseModel.transaction
    def create_card(self, **kw):
        from vilya.models.card import Card, ProjectCardCounter
        if 'board_id' not in kw:
            kw['board_id'] = self.issue_board.id
        number = ProjectCardCounter.incr(project_id=self.id)
        kw['number'] = number
        kw['project_id'] = self.id
        card = Card.create(**kw)
        return card

    def create_pull(self, **kw):
        from vilya.models.card import Card
        if 'board_id' not in kw:
            kw['board_id'] = self.issue_board.id
        kw['project_id'] = self.id
        pull = Card.create_pull(**kw)
        return pull
