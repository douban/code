define(['jquery',
 'backbone',
 'underscore',
 'modules/create_app'
 'vilya/router',
 'models/user'
 'views/layout',
 'bootstrap/dropdown'], ($, Backbone, _, createApp, Router, User, LayoutView) ->
    initCurrentUser = () ->
        currentUser = new User()
        currentUser.url = '/api/v1/current_user/'
        return currentUser
    app = createApp()
    app.initialize = () ->
      @currentUser = initCurrentUser()
      @currentUser.fetch()
      (new LayoutView()).render()
      app.router = new Router()
      Backbone.history.start()
    return app
)
