define(['jquery', 'backbone', 'underscore', 'vilya/router'], ($, Backbone, _, VilyaRouter) ->
    window.vilya =
      Models: {}
      Collections: {}
      Views: {}
      Routers: {}
      init: ->
        'use strict'
        console.log 'Hello from Backbone!'

    $ ->
      'use strict'
      window.vilya.init();

    vilyaRouter = new VilyaRouter()
    # Backbone.history.start()
)
