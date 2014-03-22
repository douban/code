define(
  ['jquery',
  'backbone',
  'underscore',
  'collections/project/menu',
  'views/partials/menu_item'],
  ($, Backbone, _, ProjectMenu, MenuItemView) ->
    MenuView = Backbone.View.extend({
      tagName: "ul"
      className: "nav nav-pills nav-stacked"
      initialize: (options) ->
        this.full_name = options.full_name
        this.collection = new ProjectMenu([
          {id: 1, title: 'files', href: '#' + this.full_name + '', active: 0}
          {id: 2, title: 'commits', href: '#' + this.full_name + '/commits', active: 0}
        ], {full_name: this.full_name})
      render: () ->
        this.views = this.collection.map(
          (item) ->
            return this.renderItem(item)
          ,
          this
        )
        return this
      renderItem: (item) ->
        view = new MenuItemView({
          model: item
        })
        this.$el.append(view.render().el)
        return view
      closeView: () ->
        _.each(this.views, (view) ->
          view.remove()
        )
        this.remove()
    })
    return MenuView
)

