define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    User = Backbone.Model.extend({
      defaults:
        password: ''
        name: ''
      url: () ->
        '/api/v1/login/'
    })
    return User
)
