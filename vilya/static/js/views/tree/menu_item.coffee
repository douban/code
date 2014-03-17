define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    _.templateSettings = {
      evaluate: /\{\{([\s\S]+?)\}\}/g
      interpolate: /\{\{=([\s\S]+?)\}\}/g
      escape: /\{\{-([\s\S]+?)\}\}/g
    }

    MenuItemView = Backbone.View.extend({
      tagName: 'li'
      className: () ->
        if this.model.get('active')
          return 'active'
        else
          return ''
      template: _.template($('#menuItemTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return MenuItemView
)

