define(
  ['jquery',
  'backbone',
  'handlebars'],
  ($, Backbone, Handlebars, Login) ->
    window.StatusView = Backbone.View.extend({
      tagName: 'div'
      template: Handlebars.compile($('#statusTemplate').html())
      initialize: (currentUser) ->
        @model = currentUser
        @model.fetch()
        @model.bind('change', _.bind(this.render, this))
      render: () ->
        @$el.html(@template(@model.toJSON()))
        $("#statusBar").html(@$el.html())
        return this
    })
    return StatusView
)

