define(
    ['jquery', 'backbone', 'underscore'],
    ($, Backbone, _) ->
        _.templateSettings = {
            evaluate: /\{\{([\s\S]+?)\}\}/g
            interpolate: /\{\{=([\s\S]+?)\}\}/g
            escape: /\{\{-([\s\S]+?)\}\}/g
        }

        ProjectCardView = Backbone.View.extend({
            tagName: 'div'
            className: 'projectContainer'
            template: _.template($('#projectTemplate').html())
            render: () ->
                this.$el.html(this.template(this.model.toJSON()))
                return this
        })
        return ProjectCardView
)

