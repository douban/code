define(
    ['jquery',
    'backbone',
    'underscore'],
    ($, Backbone, _) ->
        HomeView = Backbone.View.extend({
            tagName: 'div'
            template: _.template($('#homeTemplate').html())
            initialize: () ->
                $("#content").html(this.el)
                this.render()
            render: () ->
                this.$el.html(this.template())
                return this
        })
        return HomeView
)

