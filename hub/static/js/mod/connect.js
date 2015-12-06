define('socket.io', 'lib/socket.io.js');
define('mod/connect', ['socket.io', 'mod/node_config'], function(_, config) {
    var connectNode = function(channel) {
        var url = "http://" + config.host + ":" + config.port;
        var nodeio = io.connect(url, {
            'reconnect': true,
            'reconnection delay': 500,
            'max reconnection attempts': 10
        });
        nodeio.emit('ready', {channel: channel});
        return nodeio;
    }

    return connectNode;
});
