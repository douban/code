define(
  ['jquery',
  'views/pages/base',
  'handlebars'],
  ($, PageView, Handlebars) ->
    HomeView = PageView.extend({
      template: Handlebars.compile($('#homeTemplate').html())
      _render: () ->
        @$el.html(@template())
    })
)

