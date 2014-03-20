define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    Login = Backbone.Model.extend({
      defaults:
        password: ''
        name: ''
      url: () ->
        '/api/v1/login/'
    })
    return Login
)
