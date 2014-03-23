define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    User = Backbone.Model.extend({
      defaults:
        password: ''
        name: ''
      url: (name) ->
        name = '' if @isNew
        "/api/v1/users/#{name}"
    })
    return User
)
