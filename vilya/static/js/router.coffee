define(['jquery', 'backbone', 'underscore'], ($, Backbone, _) ->
    class VilyaRouter extends Backbone.Router
        routes: {
            "about" : "showAbout",
        },
        showAbout: () ->
            console.log "Router"
        ,
    return VilyaRouter
)
