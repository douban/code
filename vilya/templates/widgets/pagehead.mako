<%!
    from vilya.models.ticket import Ticket
    from vilya.models.project import CodeDoubanProject
    from vilya.models.team import Team
    from vilya.models.release import get_release
%>

<%def name="user_header(active)">
    <% pr_counter = user.n_open_pull_requests if user and user.n_open_pull_requests > 0 else '' %>
    <div class="subnav">
        <ul class="nav nav-pills">
            <li class="${'active' if active=='news'  else ''}"><a href="/">
                Feed
            </a></li>
            <li class="${'active' if active=='pulls' else ''}">
                <a href="/hub/my_pull_requests">
                % if request.is_mobile:
                    PRs
                % else:
                    Pull Requests
                % endif
                    % if pr_counter:
                        <span class="counter">${pr_counter}</span>
                    % endif
                </a>
            </li>
            <li class="${'active' if active=='yours' else ''} hidden-phone"><a href="/hub/yours">Your Actions</a></li>
            <li class="${'active' if active=='issues' else ''}"><a href="/hub/my_issues">Issues</a></li>
        </ul>
    </div>
</%def>

<%def name="trac_header(active, project, user, newpull=False)">
<div class="pagehead" style="${project.conf['style'].get('projhead', '')}">
    <%
        target_project = project.get_forked_from() or project
        forked_from = target_project.name
        forked_count = CodeDoubanProject.get_forked_count(project.id)
        watched_count = CodeDoubanProject.get_watched_count(project.id)
    %>
    <h1 class="pull-left">
        % if project.name == project.realname:
            <a href="/${project.name}">${project.name}</a>
        % else:
            <a href="/people/${project.owner_name}">${project.owner_name}</a> /
            <a href="/${project.name}">${project.realname}</a>
        % endif

        % if project.fork_from:
            <small class="fork-flag">
                forked from <a href="/${forked_from}">${forked_from}</a>
            </small>
        % endif

        % if project.name == project.realname:
            <% owner = project.owner %>
            <a href="${owner.url}">
                <img src="${owner.avatar_url}" title="${owner.name}" width="30" height="30" style="padding: 3px 3px 3px 10px" />
            </a>
        % endif

    </h1>
    <div class="metanav pull-right">
        % if user:
            % if not project.fork_from and user.username in ['qingfeng', 'xutao', 'xyb', 'fanjianjin', 'testuser']:
                <a class="btn minibutton hidden-phone" id="re-index" href="/${project.name}/re_index_docs">
                    Re-index
                </a>
            % endif
            <% current_ref = ref if ref else project.default_branch %>
            % if project.is_admin(user.username) and get_release(project.repository):
                <%
                    unreleased_commits_count = project.unreleased_commit_num
                    last_commit = project.repo.get_last_commit(project.default_branch)
                    last_commit_sha = last_commit.sha if last_commit else ''
                %>
                % if unreleased_commits_count < 100:
                    % if project.name == "ilmen":
                        <a class="btn minibutton" id="go-release-btn" href="http://up.dapps.douban.com/release/ilmen">
                            Go Release
                        </a>
                    % else:
                        <a class="btn minibutton hidden-phone" id="not-released-btn" \
                        href="http://bridge.dapps.douban.com/app/${project.name}/deploy#${last_commit_sha}">Not Released</a>
                    % endif
                    <span class="counts-label" id="unreleased-commits-count">
                        ${unreleased_commits_count}
                    </span>
                % endif
            % endif
            <a class="btn minibutton" id="issue-btn" href="/${project.name}/issues/new">New Issue</a>
            % if project.has_push_perm(user.username):
                <a class="btn minibutton" id="pullrequest-btn" href="/${project.name}/pull/new?head_ref=${current_ref}">Pull Request</a>
            % endif

            % if project.is_mirror_project:
                <a class="btn minibutton" id="fetch-btn" proj_id=${project.id}>Fetch</a>
            % endif

            % if CodeDoubanProject.has_watched(project.id, user):
                <a class="btn minibutton unwatch" id="watch-btn" proj_id=${project.id}>Unwatch</a>
            % else:
                <a class="btn minibutton watch" id="watch-btn" proj_id=${project.id}>Watch</a>
            % endif

            <span class="counts-label" id="watched-count"><a href="/${project.name}/watchers">${watched_count}</a></span>
            <% is_empty = project.repo.is_empty %>
            % if not is_empty and not (project.is_owner(user) and "/" in project.name):
                <a class="btn minibutton" id="fork-btn" href="/hub/create?fork_from=${project.id}">Fork</a>
                <span class="counts-label forked"><a href="/${project.name}/forkers">${forked_count}</a></span>
            % endif
        % endif
    </div>
    <div class="clearfix"></div>
</div>
<div id="mainnav" class="subnav">
    <ul class="nav nav-pills">
        <li class="${'active' if active == 'source' else ''} first"><a href="/${project.name}">Code</a></li>
        % for dname, dpath, ddisp, _ in project.doc_tabs():
            <li class="${'active' if active == dname else ''} hidden-phone"><a class="tab_docs" href="/${project.name}${dpath}">${ddisp}</a></li>
        % endfor
        <li class="${'active' if active == 'pulls' else ''}">
            <a href="/${project.name}/pulls">
                % if request.is_mobile:
                    PRs
                % else:
                    Pull Requests
                % endif
                <% opened_tickets = [t for t in Ticket.gets_by_proj(project.id) if t.closed is None] %>
                <span class="counter">${len(opened_tickets)}</span>
            </a>
        </li>
        <li class="${'active' if active == 'issues' else ''}">
            <a href="/${project.name}/issues">Issues
                <span class="counter">${'%s' % project.n_open_issues}</span>
            </a>
        </li>

        % if project.is_owner(user):
            <li class="${'active' if active == 'settings' else ''}"><a href="/${project.name}/settings" >Settings</a></li>
        % endif
        <li class="${'active' if active == 'graph' else ''} hidden-phone"><a href="/${project.name}/graph" >Graphs</a></li>
    </ul>
</div>

% if active == 'source':
    <div id="project-info">
        <div class="summary">
        <%include file="/widgets/repository_lang_stats.html" args="repo=project"/>
        % if project.summary:
            <p>${project.summary}</p>
        % else:
            <p>这个家伙比较懒，目前此项目没有任何描述...</p>
        % endif
        </div>
        <% teams = Team.gets_by_project_id(project.id) %>
        % if teams:
            <div class="team-label">
                <strong>Team:</strong>
                % for team in teams:
                    <span><a href="/hub/team/${team.uid}">${team.name}</a></span>
                % endfor
            </div>
        % endif
        <div id="git-url" class="git-url http">
            <div class="btn-group">
                <button id="git-label" type="button" class="btn">HTTP</button>
                <button type="button" class="btn dropdown-toggle" data-toggle="dropdown">
                    <span class="caret"></span>
                </button>
                <ul class="dropdown-menu" role="menu">
                    <li><a id="http" href="#">HTTP</a></li>
                    <li><a id="ssh" href="#">SSH</a></li>
                </ul>
            </div>
            <div id="http-url" class="http-url">
                <input type="text" class="git-url" value="${project.repository}" readonly />
                <a class="copy-git-url" data-clipboard-text="${project.repository}" data-copied-hint="copied!" data-copy-hint="Copy git url"><img src="/static/img/clippy.png" /></a>
            </div>
            <div id="ssh-url" class="ssh-url">
                <input type="text" class="git-url" value="${project.ssh_repository}" readonly />
                <a class="copy-git-url" data-clipboard-text="${project.ssh_repository}" data-copied-hint="copied!" data-copy-hint="Copy git url"><img src="/static/img/clippy.png" /></a>
                Beta, please do not use in production.
            </div>
        </div>
    </div>
% endif
</%def>
