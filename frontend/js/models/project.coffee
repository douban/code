define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    Project = Backbone.Model.extend({
      defaults:
        id: null
        description: ''
        name: ''
        full_name: ''
        owner_name: ''
        owner_id: null
      url: () ->
        "/api/v1/projects/#{@get('full_name')}"
    })
)
