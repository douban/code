define(['jquery',
 'backbone',
 'underscore',
 'vilya/app',
 'vilya/router',
 'models/user'
 'views/status',
 'bootstrap/dropdown'], ($, Backbone, _, app, Router, User, StatusView) ->

  initialize = () ->
    app.currentUser = new User
    (new StatusView(app.currentUser)).render()
    Router.initialize(app)

  return {
    initialize: initialize
  }
)
