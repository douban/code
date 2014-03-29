define [
  'jquery'
  'views/pages/projects/base'
  'underscore'
  'handlebars'
  'views/partials/files'
  'views/partials/readme'
], ($, ProjectBaseView, _, Handlebars, FilesView, ReadmeView) ->
  ProjectShowView = ProjectBaseView.extend({
    readmeContainer: () -> @$el.find('#project-readme')
    basicContainer: () -> @$el.find('#project-basic')
    _render: () ->
      @render_project_layout()
      new FilesView(project: @project, el: @basicContainer())
      new ReadmeView(project: @project, el: @readmeContainer())
  })
  return ProjectShowView
