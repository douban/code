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
    _initialize: (options) ->
      this.full_name = options.full_name
    _render: () ->
      @$el.html(@template())
      this.menuView = this.renderMenu()
      @renderFile(@full_name)
      @renderReadme(@full_name)
    renderFile: (full_name) ->
      new TreeFileView(full_name: full_name)
    renderMenu: () ->
      view = new MenuView({full_name: this.full_name})
      $el = this.$el.find('#project-menu')
      $el.append(view.render().el)
      return view
    renderReadme: (full_name) ->
      window.view = new ReadmeView(full_name: full_name)
    closeView: () ->
      _.each(this.views, (view) ->
        view.remove()
      )
      this.menuView.closeView()
      this.readmeView.remove()
      this.remove()
  })
  return ProjectShowView
