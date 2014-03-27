define(
  ['jquery',
  'backbone',
  'underscore',
  'handlebars',
  ], ($, Backbone, _, Handlebars) ->
    MenuView = Backbone.View.extend({
      template: Handlebars.compile($('#projectMenuTemplate').html())
      initialize: (options) ->
        @setElement(options.el)
        @full_name = options.full_name
        @$container = options.container
        @collection = [
          {title: 'Files', path: '#' + this.full_name + ''}
          {title: 'Commits', path: '#' + this.full_name + '/commits'}
        ]
        @render()
      render: () ->
        @$el.html(@template(items: @collection))
      closeView: () ->
        this.remove()
    })
    return MenuView
)

