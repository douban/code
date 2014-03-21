define([
  'jquery',
  'backbone',
  'handlebars',
  'views/partial_views/status'],
  ($, Backbone, Handlebars, StatusView) ->
    Backbone.View.extend({
      initialize: (app) ->
        (new StatusView(app.currentUser)).render()
    })
)
