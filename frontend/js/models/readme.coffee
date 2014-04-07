define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    Readme = Backbone.Model.extend({
      defaults:
        html: ''
      url: () ->
        '/api/v1/projects/' + this.full_name + '/readme/'
      initialize: (options) ->
        this.full_name = options.full_name
    })
    return Readme
)
