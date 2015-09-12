require.config({
    baseUrl: '/js/'
});
define('raven', 'lib/raven-1.0.8.js');

require(
    ['raven'],
    function(Raven) {
        // app.yaml
        var sentry_dsn = "http://dda66d28e34741e6ba430d44deebbeba@onimaru-stable.intra.douban.com/10";
        var options = {
            includePaths: [/https?:\/\/code\.dapps\.douban\.com/]
        };
        Raven.config(sentry_dsn, options).install();
    }
)
