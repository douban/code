define(
  ['jquery', 'backbone', 'handlebars', 'models/readme'],
  ($, Backbone, Handlebars, Readme) ->

    ReadmeView = Backbone.View.extend({
      template: Handlebars.compile($('#readmeTemplate').html())
      initialize: (options) ->
        @model = new Readme({full_name: options.full_name})
        @model.bind('change', _.bind(this.render, this))
        @model.fetch()
      render: () ->
        @$el.html(this.template(@model.toJSON()))
        $("#project-readme").html(@el)

    })
    return ReadmeView
)
