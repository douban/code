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
        "/api/v1/projects/#{@get('full_name')}/"
      clone_url: () ->
        # TODO: replace hardcode, get server address via system var
        "http://localhost:8000/#{@get('full_name')}.git"
      toFullJSON: () ->
        json = @toJSON()
        _.extend(json, {clone_url : @clone_url()})
    })
)
