define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    Commit = Backbone.Model.extend({
      defaults:
        id: 0
        type: 'commit'
        name: ''
        email: ''
        parents: []
        date: ''
        message: ''
    })
    return Commit
)

