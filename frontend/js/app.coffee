define(['jquery',
 'backbone',
 'underscore',
 'modules/create_app'
 'vilya/router',
 'models/user'
 'views/layout',
 'bootstrap/dropdown'], ($, Backbone, _, createApp, Router, User, LayoutView) ->
    app = createApp()
    app.initialize = () ->
      @currentUser = new User()
      (new LayoutView()).render()
      app.router = new Router()
      Backbone.history.start()
    return app
)
