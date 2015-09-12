# -*- coding: utf-8 -*-

from vilya.models.issue import Issue
from vilya.models.project_issue import ProjectIssue
from vilya.models.team_issue import TeamIssue
from vilya.models.fair_issue import FairIssue


# map of issue type <-> class
ISSUE_TYPE_CLASS = {'team': TeamIssue,
                    'project': ProjectIssue,
                    'default': Issue,
                    'fair': FairIssue}
