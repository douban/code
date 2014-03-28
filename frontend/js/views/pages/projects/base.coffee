define [
  'jquery'
  'views/pages/base'
  'underscore'
  'handlebars'
  'models/project'
  'views/partials/menu'
], ($, PageView, _, Handlebars, Project, MenuView) ->
  ProjectBaseView = PageView.extend({
    template: Handlebars.compile($('#projectBaseTemplate').html())
    menuContainer: () -> @$el.find('#project-menu')
    _initialize: (options) ->
      @full_name = options.full_name
      @project = new Project(full_name: @full_name)
      @project.fetch()
    render_project_layout: () ->
      @$el.html(@template())
      new MenuView(project: @project, el: @menuContainer())
    closeView: () ->
      @remove()
  })
