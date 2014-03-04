define(['jquery',
 'backbone',
 'underscore',
 'vilya/app',
 'vilya/router',
 'bootstrap/dropdown'], ($, Backbone, _, app, Router) ->

    initialize = () ->
        Router.initialize(app)

    return {
        initialize: initialize
    }
)
