define(
  ['jquery',
  'backbone',
  'handlebars'],
  ($, Backbone, Handlebars) ->
    StatusView = Backbone.View.extend({
      tagName: 'div'
      template: Handlebars.compile($('#statusTemplate').html())
      initialize: () ->
        @model = app.currentUser
        @model.bind('change', _.bind(this.render, this))
      render: () ->
        @$el.html(@template(@model.toJSON()))
        $("#statusBar").html(@$el.html())
        return this
      removeCurrentUser: (events) ->
        event.preventDefault()
        app.currentUser.destroy()
    })
    return StatusView
)
