define(
  ['jquery',
  'views/pages/base',
  'handlebars'],
  ($, PageView, Handlebars) ->
    HomeView = PageView.extend({
      tagName: 'div'
      template: Handlebars.compile($('#homeTemplate').html())
      _render: () ->
        @$el.html(this.template())
    })
    return HomeView
)

