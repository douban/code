define(
  ['jquery',
  'backbone',
  'handlebars',
  'models/login'],
  ($, Backbone, Handlebars, Login) ->
    login = new Login()
    window.StatusView = Backbone.View.extend({
      model: login
      tagName: 'div'
      template: Handlebars.compile($('#statusTemplate').html())
      initialize: () ->
        @model.fetch()
        this.model.bind('change', _.bind(this.render, this))
      render: () ->
        @$el.html(@template(@model.toJSON()))
        $("#statusBar").html(@$el.html())
        return this
    })
    return StatusView
)

