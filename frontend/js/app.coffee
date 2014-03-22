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
      window.app = app
      app.currentUser = new User()
      (new LayoutView(app)).render()
      new Router(app)
      Backbone.history.start()

    return {
      initialize: initialize
    }
)
