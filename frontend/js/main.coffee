define(['jquery',
 'backbone',
 'underscore',
 'vilya/app',
 'vilya/router',
 'views/status',
 'bootstrap/dropdown'], ($, Backbone, _, app, Router, StatusView) ->

  initialize = () ->
    Router.initialize(app)
    v = (new StatusView())

  return {
    initialize: initialize
  }
)
