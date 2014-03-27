define(
  ['jquery',
  'backbone',
  'handlebars'],
  ($, Backbone, Handlebars) ->
    StatusView = Backbone.View.extend({
      template: Handlebars.compile($('#statusTemplate').html())
      initialize: (options) ->
        @setElement(options.el)
        @model = app.currentUser
        @model.bind('change', _.bind(this.render, this))
      render: () ->
        @$el.html(@template(@model.toJSON()))
        return this
    })
    return StatusView
)
