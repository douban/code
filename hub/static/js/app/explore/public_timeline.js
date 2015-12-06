require(['jquery'
, 'mod/connect'
, 'mod/count'
, 'mod/relative_date'
, 'mod/user_avatar'
, 'mod/user_profile_card'
, 'mod/newsfeed'
, 'mod/newsfeed_pagination'
], function($, connectNode, countDict, updateRelativeDate, loadAvatar){
    //put your home code here.
    var channel = 'feed:public:everyone:v2';
    var io = connectNode(channel);
    io.on('announce', function(data) {
          countDict.public_num += 1;
          if ($('.timeline>ul').length == 0) {
              $('.info').hide();
              $('body>.container').prepend(
              '<div class="timeline"><h2>Public Timeline Feed</h2><ul></ul></div>' 
              );
          }
          $('.timeline>ul').prepend(data.send_message);
          updateRelativeDate();
          loadAvatar();
    });
});
