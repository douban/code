# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime, timedelta
from quixote.errors import TraversalError

from vilya.libs.template import st
from vilya.views.util import jsonize
from vilya.models.project import CodeDoubanProject

_q_exports = []


class GraphUI:
    _q_exports = ['setting', 'commits', 'data']

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def _q_index(self, request):
        errors = ''
        project_name = self.proj_name
        user = request.user
        project = CodeDoubanProject.get_by_name(project_name)
        if not project:
            raise TraversalError()
        data = project.git.get_gitstats_data()
        return st('graph.html', **locals())

    def _q_lookup(self, request):
        project_name = self.proj_name
        project = CodeDoubanProject.get_by_name(project_name)
        if not project:
            raise TraversalError()
        return request.redirect('/%s/graph' % project_name)

    @jsonize
    def commits(self, request):
        project = CodeDoubanProject.get_by_name(self.proj_name)
        peak, year_week_act = project.git.get_year_week_act_stats()

        WEEKS = 26  # show previous 26 weeks from now
        deltaweek = timedelta(7)
        stampcur = datetime.now()
        commits = []
        for i in range(WEEKS):
            week = stampcur.strftime('%Y-%W')
            commits.append(
                float(year_week_act.get(week, 0)) / float(peak or 1))
            stampcur -= deltaweek

        # TODO: collect commits stats by owner
        return {'total': WEEKS, 'all': commits[::-1]}

    @jsonize
    def data(self, request):
        project_name = self.proj_name
        project = CodeDoubanProject.get_by_name(project_name)
        data = project.git.get_gitstats_data()

        json = {}
        json['activity'] = graph_activity(data)
        json['commits'] = graph_commits(data)
        json['extensions'] = graph_extensions(data)
        json['lines'] = graph_lines(data)
        return json


def graph_activity(data):
    # Weekly activity
    from datetime import datetime, timedelta
    WEEKS = 26
    # generate weeks to show (previous N weeks from now)
    now = datetime.now()
    deltaweek = timedelta(7)
    weeks = []
    stampcur = now
    for i in range(0, WEEKS):
        weeks.insert(0, stampcur.strftime('%Y-%W'))
        stampcur -= deltaweek
    commits = []
    for i in range(0, WEEKS):
        if weeks[i] in data.year_week_act:
            commits.append({
                "week": i, "commits": data.year_week_act[weeks[i]],
                "commits_peak": data.year_week_act_peak})
        else:
            commits.append({
                "week": i, "commits": 0,
                "commits_peak": data.year_week_act_peak})
    return {"data": commits}


def graph_extensions(data):
    extensions = data.extensions
    total_f = data.source_files
    total_l = data.source_lines
    newdata = []
    for k in extensions:
        f_num = extensions[k]['files']
        l_num = extensions[k]['lines']
        try:
            loc_p = (100.0 * l_num) / total_l
        except:
            loc_p = 0
        try:
            foc_p = (100.0 * f_num) / total_f
        except:
            foc_p = 0
        newdata.append({'name': k or 'other',
                        'files': f_num,
                        'lines': l_num,
                        'value': l_num,
                        'loc_p': "%.1f" % loc_p,
                        'foc_p': "%.1f" % foc_p,
                        })
    return {"data": newdata}


def graph_lines(data):
    import operator
    from datetime import datetime
    from itertools import groupby
    changes = data.changes_by_date
    lines = sorted(changes.iteritems(), key=operator.itemgetter(0))
    func = lambda x: (datetime.fromtimestamp(x[0]).strftime('%Y-%m-%d'), x[1])
    lines = map(func, lines)
    newlines = []
    lines = groupby(lines, lambda x: x[0])
    for label, c in lines:
        ele = list(c)[-1]
        line_num = ele[1]['lines']
        newlines.append({'date': ele[0], 'lines': line_num})
    return {"data": newlines}


def graph_commits(data):
    from datetime import datetime
    from copy import deepcopy
    authors = data.getAuthors(10)
    changes = data.changes_by_date_by_author
    newdata = {}
    result = []
    commits_per_author = {}
    for author in authors:
        commits_per_author[author] = 0
    for stamp in sorted(changes.keys()):
        nstamp = datetime.fromtimestamp(stamp).strftime('%Y-%m-%d')
        for author in authors:
            if author in changes[stamp].keys():
                commits_per_author[author] = changes[stamp][author]['commits']
        adict = deepcopy(commits_per_author)
        newdata[nstamp] = adict
    for k in sorted(newdata.keys()):
        x = newdata[k]
        x.update({'date': k})
        result.append(x)
    return {"data": result, "authors": authors}
