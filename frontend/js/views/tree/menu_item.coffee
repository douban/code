define(
  ['jquery', 'backbone', 'handlebars'],
  ($, Backbone, Handlebars) ->
    MenuItemView = Backbone.View.extend({
      tagName: 'li'
      className: () ->
        if this.model.get('active')
          return 'active'
        else
          return ''
      template: Handlebars.compile($('#menuItemTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return MenuItemView
)

