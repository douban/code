define [
  'jquery'
  'views/pages/base'
  'underscore'
  'handlebars'
  'views/partials/menu'
], ($, PageView, _, Handlebars, MenuView) ->
  ProjectBaseView = PageView.extend({
    template: Handlebars.compile($('#projectBaseTemplate').html())
    menuContainer: () -> @$el.find('#project-menu')
    _initialize: (options) ->
      this.full_name = options.full_name
    render_project_layout: () ->
      @$el.html(@template())
      new MenuView(full_name: @full_name, el: @menuContainer())
    closeView: () ->
      this.remove()
  })
