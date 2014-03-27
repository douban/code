define(
  ['jquery',
  'backbone',
  'underscore',
  'handlebars',
  ], ($, Backbone, _, Handlebars) ->
    MenuView = Backbone.View.extend({
      tagName: "ul"
      className: "nav nav-pills nav-stacked"
      template: Handlebars.compile($('#projectMenuTemplate').html())
      initialize: (options) ->
        @full_name = options.full_name
        @$container = options.container
        @collection = [
          {title: 'Files', path: '#' + this.full_name + ''}
          {title: 'Commits', path: '#' + this.full_name + '/commits'}
        ]
        @$container.html(@el)
        @render()
      render: () ->
        @$el.html(@template(items: @collection))
      closeView: () ->
        this.remove()
    })
    return MenuView
)

