define([
  'jquery',
  'backbone',
  'handlebars',
  'views/partials/status'],
  ($, Backbone, Handlebars, StatusView) ->
    Backbone.View.extend({
      initialize: () ->
      render: () ->
        (new StatusView()).render()
    })
)
