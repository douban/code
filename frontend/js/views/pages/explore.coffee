define([
  'jquery',
  'views/pages/base',
  'underscore',
  'collections/projects',
  'views/partials/list'],
  ($, PageView, _, Projects, ProjectListView) ->
    ExploreView = PageView.extend({
      template: Handlebars.compile($('#exploerTemplate').html())
      listContainer: () -> @$el.find('#project-list')
      _initialize: () ->
      _render: () ->
        @$el.html(@template())
        window.view = new ProjectListView(el: @listContainer())
    })
)


