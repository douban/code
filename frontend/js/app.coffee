define(['jquery',
 'backbone',
 'underscore',
 'modules/create_app'
 'vilya/router',
 'models/user'
 'views/status',
 'bootstrap/dropdown'], ($, Backbone, _, createApp, Router, User, StatusView) ->
  initialize = () ->
    app = createApp()
    app.currentUser = new User
    (new StatusView(app.currentUser)).render()
    Router.initialize(app)

  return {
    initialize: initialize
  }
)
