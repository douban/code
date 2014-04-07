define(
  ['jquery', 'backbone', 'underscore', 'models/project'],
  ($, Backbone, _, Project) ->
    Projects = Backbone.Collection.extend({
      model: Project
      url: '/api/v1/projects/'

    })
    return Projects
)
