define(
  ['jquery', 'backbone', 'handlebars', 'models/readme'],
  ($, Backbone, Handlebars, Readme) ->

    ReadmeView = Backbone.View.extend({
      template: Handlebars.compile($('#readmeTemplate').html())
      initialize: (options) ->
        @model = new Readme({full_name: options.full_name})
        @$container = options.container
        @model.bind('change', _.bind(this.render, this))
        @model.fetch()
        @$container.html(@el)
      render: () ->
        $(@el).html(this.template(@model.toJSON()))
    })
    return ReadmeView
)
