define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    Login = Backbone.Model.extend({
      defaults:
        email: ''
        password: ''
        username: ''
        avatar: ''
      url: () ->
        '/api/v1/login/'
    })
    return Login
)
