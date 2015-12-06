require(['jquery'
, 'mod/connect'
, 'mod/count'
, 'mod/relative_date'
, 'mod/user_avatar'
], function($, connectNode, countDict, updateRelativeDate, loadAvatar){
   var username = $('#get-username').attr('data-username');
   var channel = 'feed:private:user:v2:' + username;
   var io = connectNode(channel);
   io.on('announce', function(data) {
       countDict.userfeed_num += 1;
       $('.timeline>ul').prepend(data.send_message);
       updateRelativeDate();
       loadAvatar();
   });
});
