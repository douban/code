define [
  'jquery'
  'views/pages/projects/base'
  'underscore'
  'handlebars'
  'views/partials/basic'
  'views/partials/readme'
], ($, ProjectBaseView, _, Handlebars, BasicView, ReadmeView) ->
  ProjectShowView = ProjectBaseView.extend({
    readmeContainer: () -> @$el.find('#project-readme')
    basicContainer: () -> @$el.find('#project-basic')
    _render: () ->
      @render_project_layout()
      new BasicView(project: @project, el: @basicContainer())
      new ReadmeView(project: @project, el: @readmeContainer())
  })
  return ProjectShowView
