define('socket.io', 'lib/socket.io.js');
define('mod/liveupdate', [
  'jquery',
  'jquery-tmpl',
  'socket.io'
], function ($, _) {
    //var server = 'http://doubandev2.intra.douban.com:7076';
    var server = 'http://code.intra.douban.com:7076';
    var live = io.connect(server, {
      'reconnect': true,
      'reconnection delay': 500,
      'max reconnection attempts': 10
    });

    var roomPeoples = {};
    live.on('announce', function(data){
      var user = data.username;
      if(user !== undefined && user in roomPeoples === false) {
        roomPeoples[user] = user;
        var user_html = '<a class="avatar tooltipped downwards"><img height="24" width="24" alt="'+user+'" src="'+data.avatar+'"></a>';
        $('#room_peoples .quickstat').show();
        $('#room_peoples').append(user_html);
      }

      if(data.type === 'typing') {
        $('#typing').show();
        $('#typing span').html(data.username+' is typing......');
      }
      else if(data.type === 'merge') {
        $(".pull-state span").html("Merged");
        $(".merge-guide").hide();
        var merged_time = new Date();
        $("#changelog").append($.tmpl($("#render_node_merge"),
                                      {'merged_time': merged_time,
                                       'user':data.username,
                                       'avatar': data.avatar}));
      }
      else {
        $('#typing').hide();
        $('#changelog').append(data.message);
      }
    });

    return live;
});
