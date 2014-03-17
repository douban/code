define(
  ['jquery', 'backbone', 'underscore',
  'models/menu_item'],
  ($, Backbone, _, MenuItem) ->
    ProjectMenu = Backbone.Collection.extend({
      model: MenuItem
    })
    return ProjectMenu
)
