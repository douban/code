define [
  'jquery'
  'views/pages/base'
  'underscore'
  'models/project'
  'views/partials/file'
  'views/partials/menu'
  'views/partials/readme'
], ($, PageView, _, Project, TreeFileView, MenuView, ReadmeView) ->
  ProjectIndexView = PageView.extend({
    tagName: 'div'
    className: 'row'
    _initialize: (options) ->
      this.full_name = options.full_name
    _render: () ->
      this.$el.append('<div id="project-menu" class="col-sm-2"></div><div id="project-content" class="col-sm-10"></div><div id="project-readme" class="col-sm-10"></div>')
      this.menuView = this.renderMenu()
      $el = this.$el.find('#project-content')
      $el.append($('#treeTemplate').html())
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
      window.view = new ReadmeView({full_name: full_name})
    closeView: () ->
      _.each(this.views, (view) ->
        view.remove()
      )
      this.menuView.closeView()
      this.readmeView.remove()
      this.remove()
  })
  return ProjectIndexView
