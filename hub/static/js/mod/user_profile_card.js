define('mod/user_profile_card', [
    'jquery',
    'jquery-tmpl'
], function($) {
    $(function () {
        var userCard, teamCard, users = {}, user_type = {};
        $(document).delegate(
            '.user-link,.user-mention', 'mouseover',
            function (e) {
                if (!userCard) {
                    userCard = $('<div class="user-card"></div>').appendTo('body')
                        .mouseleave(function () {
                            $(this).hide();
                            $('.team-card').hide();
                        });
                }
                if (!teamCard) {
                    teamCard = $('<div class="team-card"></div>').appendTo('body')
                        .mouseleave(function () {
                            $(this).hide();
                            $('.user-card').hide();
                        });
                }
                var pos = $(this).offset();
                pos.left = pos.left - 5;
                pos.top = pos.top - 5;
                var name = /@?(\w+)/.exec($(this).text())[1], user = users[name];

                if (!user) {
                    $.getJSON('/api/card_info', {user: name},
                              function (r) {
                                  if (r.team) {
                                      teamCard.css(pos).empty().show();
                                      teamCard.append($.tmpl($('#templ-team-card'), r.team));
                                      user_type[name] = 'team';
                                      users[name] = r.team;
                                  } else {
                                      userCard.css(pos).empty().show();
                                      userCard.append($.tmpl($('#templ-user-card'), r.user));
                                      user_type[name] = 'user';
                                      users[name] = r.user;
                                  }
                              });
                } else {
                    if (user_type[name] === 'team') {
                        teamCard.css(pos).empty().show();
                        teamCard.append($.tmpl($('#templ-team-card'), user));
                    } else {
                        userCard.css(pos).empty().show();
                        userCard.append($.tmpl($('#templ-user-card'), user));
                    }
                }
            });
    });
});
