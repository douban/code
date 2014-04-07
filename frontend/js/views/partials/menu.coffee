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
        full_name = options.project.get('full_name')
        @collection = [
          {title: 'Files', path: '#' + full_name + ''}
          {title: 'Commits', path: '#' + full_name + '/commits'}
        ]
        @render()
      render: () ->
        @$el.html(@template(items: @collection))
      closeView: () ->
        this.remove()
    })
    return MenuView
)

