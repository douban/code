define(['jquery',
 'backbone',
 'underscore',
 'modules/create_app'
 'vilya/router',
 'models/user'
 'views/layout',
 'bootstrap/dropdown'], ($, Backbone, _, createApp, Router, User, LayoutView) ->
  initialize = () ->
    app = createApp()
    app.currentUser = new User()
    (new LayoutView(app)).render()
    Router.initialize(app)

  return {
    initialize: initialize
  }
)
