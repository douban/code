define([
  'jquery',
  'views/pages/projects/base',
  'underscore',
  'models/project',
  'views/partials/commits',
  'views/partials/menu'],
  ($, ProjectBaseView, _, Project, CommitView, MenuView) ->
    ProjectCommitsView = ProjectBaseView.extend({
      commitsContainer: () -> @$el.find('#project-commits')
      _render: () ->
        @render_project_layout()
        new CommitView(full_name: @full_name, el: @commitsContainer())
    })
    return ProjectCommitsView
)

