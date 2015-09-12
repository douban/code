define('store', 'lib/store.js');
define('mod/user_following', [
    'jquery',
    'store'
], function($, store) {
  var API_USER_FOLLOWING_PATH = "/api/user/following"
  var USER_FOLLOWING_KEY = "user-following";
  var USER_FOLLOWING_UPDATE_KEY= "date:user-following"
  var ONE_DAY_IN_SECONDS = 60*60*24;

  var update = function() {
    var currentTime = new Date().getTime();
    var lastTime = store.get(USER_FOLLOWING_UPDATE_KEY);
    if (lastTime && (currentTime - lastTime) < ONE_DAY_IN_SECONDS ) {
      return;
    }

    $.ajax(
      API_USER_FOLLOWING_PATH
    ).done(function(users){
      var following = $.map(users, function(item){
        return item["username"];
      });
      store.set(USER_FOLLOWING_KEY, following);
      store.set(USER_FOLLOWING_UPDATE_KEY, currentTime);
    }).fail(function(jqxhr, textStatus, error){
      return;
    });
  }

  return {
    update: update,
    val: function(){
      return store.get(USER_FOLLOWING_KEY) || [];
    }
  };

});
