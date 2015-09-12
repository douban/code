require(['jquery'
, 'mod/connect'
, 'mod/count'
, 'mod/relative_date'
, 'mod/user_avatar'
, 'mod/user_profile_card'
], function($, connectNode, countDict, updateRelativeDate, loadAvatar) {
    var btn = $('.join-or-leave-btn');
    if (btn.length == 0) {
        btn = $('.btn-success');
    }
    var team_id = btn.attr("data-teamid");
    var channel = 'feed:public:team:v2:' + team_id;
    var io = connectNode(channel);
    io.on('announce', function(data) {
        countDict.teamfeed_num += 1;
        $('.timeline>ul').prepend(data.send_message);
        updateRelativeDate();
        loadAvatar();
    });
});
