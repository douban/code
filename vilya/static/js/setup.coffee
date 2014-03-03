require.config(
    {
        baseUrl: "/js/lib/",
        distUrl: "/static/dist/js/lib/",
        aliases: {
            'vilya': '../'
            'views': '../views/'
            'collections': '../collections/'
            'models': '../models/'
            'modules': '../modules/'
        }
    }
)

define('jquery-src', 'jquery/jquery.js')
define('jquery', ['jquery-src'], () ->
    return window.jQuery;
)

define('backbone-src', 'backbone/backbone.js')
define('backbone', ['backbone-src'], () ->
    Backbone.inhert = Backbone.View.extend
    return Backbone
)

define('backbone/events', ['backbone-src'], () ->
    return Backbone.Events
)

require(['vilya/main'], (App) ->)
