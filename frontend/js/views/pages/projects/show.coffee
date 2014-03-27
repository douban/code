define [
  'jquery'
  'views/pages/base'
  'underscore'
  'handlebars'
  'views/partials/files'
  'views/partials/menu'
  'views/partials/readme'
], ($, PageView, _, Handlebars, FilesView, MenuView, ReadmeView) ->
  ProjectShowView = PageView.extend({
    tagName: 'div'
    className: 'row'
    template: Handlebars.compile($('#projectShowTemplate').html())
    menuContainer: () -> @$el.find('#project-menu')
    readmeContainer: () -> @$el.find('#project-readme')
    _initialize: (options) ->
      this.full_name = options.full_name
    _render: () ->
      @$el.html(@template())
      @renderFile(@full_name)
      @renderReadme(@full_name)
      @renderMenu(@full_name)
    renderFile: (full_name) ->
      new FilesView(full_name: full_name)
    renderMenu: (full_name) ->
      new MenuView(full_name: full_name, el: @menuContainer())
    renderReadme: (full_name) ->
      new ReadmeView(full_name: full_name, el: @readmeContainer())
    closeView: () ->
      this.remove()
  })
  return ProjectShowView
