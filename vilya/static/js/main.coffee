define(['jquery',
 'backbone',
 'underscore',
 'vilya/router',
 'bootstrap/dropdown'], ($, Backbone, _, VilyaRouter) ->
    window.vilya =
      Models: {}
      Collections: {}
      Views: {}
      Routers: {}
      init: ->
        'use strict'
        console.log 'Hello from Backbone!'
        vilyaRouter = new VilyaRouter()

    $ ->
      'use strict'
      window.vilya.init();

    Backbone.history.start()
)
