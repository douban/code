define [
  'jquery'
  'views/pages/base'
  'underscore'
  'models/project'
  'models/readme'
  'collections/project/files'
  'views/partials/file'
  'views/partials/menu'
  'views/partials/readme'
], ($, PageView, _, Project, Readme, ProjectFiles, TreeFileView, MenuView, ReadmeView) ->
  ProjectIndexView = PageView.extend({
    tagName: 'div'
    className: 'row'
    _initialize: (options) ->
      this.full_name = options.full_name
      this.fileCollection = new ProjectFiles({full_name: this.full_name})
      this.fileCollection.fetch({reset: true})
      this.listenTo(this.fileCollection, 'reset', this.render)
    _render: () ->
      this.$el.append('<div id="project-menu" class="col-sm-2"></div><div id="project-content" class="col-sm-10"></div>')
      this.menuView = this.renderMenu()
      $el = this.$el.find('#project-content')
      $el.append($('#treeTemplate').html())
      this.views = this.fileCollection.map(
        (item) ->
          return this.renderFile(item)
        ,
        this
      )
      this.readmeView = this.renderReadme()
    renderFile: (item) ->
      view = new TreeFileView({
        model: item
      })
      $el = this.$el.find('#project-tree')
      $el.append(view.render().el)
      return view
    renderMenu: () ->
      view = new MenuView({full_name: this.full_name})
      $el = this.$el.find('#project-menu')
      $el.append(view.render().el)
      return view
    renderReadme: () ->
      model = new Readme({full_name: this.full_name})
      view = new ReadmeView({
        full_name: this.full_name
        model: model
      })
      $el = this.$el.find('#project-content')
      this.listenTo(model, 'change', () ->
        $el.append(view.render().el)
      )
      model.fetch()
      return view
    closeView: () ->
      _.each(this.views, (view) ->
        view.remove()
      )
      this.menuView.closeView()
      this.readmeView.remove()
      this.remove()
  })
  return ProjectIndexView
