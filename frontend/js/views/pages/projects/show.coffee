define [
  'jquery'
  'views/pages/base'
  'underscore'
  'handlebars'
  'views/partials/file'
  'views/partials/menu'
  'views/partials/readme'
], ($, PageView, _, Handlebars, TreeFileView, MenuView, ReadmeView) ->
  ProjectShowView = PageView.extend({
    tagName: 'div'
    className: 'row'
    template: Handlebars.compile($('#projectShowTemplate').html())
    menuContainer: () -> @$el.find('#project-menu')
    _initialize: (options) ->
      this.full_name = options.full_name
    _render: () ->
      @$el.html(@template())
      @renderFile(@full_name)
      @renderReadme(@full_name)
      @renderMenu(@full_name)
    renderFile: (full_name) ->
      new TreeFileView(full_name: full_name)
    renderMenu: (full_name) ->
      new MenuView({full_name: full_name, container: @menuContainer()})
    renderReadme: (full_name) ->
      new ReadmeView(full_name: full_name)
    closeView: () ->
      this.remove()
  })
  return ProjectShowView
