
require.config({ enable_ozma: true });


/* @source mod/count.js */;

define('mod/count', [], function() {
    var countDict = {
        public_num: 35,
        teamfeed_num: 35,
        userfeed_num: 35,
    };
    return countDict;
});

/* @source mod/user_avatar.js */;

define('mod/user_avatar', [
  "jquery",
  "jquery-lazyload"
], function($, _) {
    var isRetinaDisplay = window.devicePixelRatio > 1;

    var patchForRetina = function(originalURL) {
      var match = /^(.+\Ws=)(\d+)(.*)$/.exec(originalURL);
      if (match === null) {
        return originalURL;
      }

      var oldSize = parseInt(match[2], 10);
      var newSize = Math.ceil(window.devicePixelRatio * oldSize);

      return match[1] + newSize.toString(10) + match[3];
    };

    var checkLoad = function() {
        var e = $(this);
        if (isRetinaDisplay) {
            var dataOriginalURL = e.attr('data-original') || e.attr('src');
            e.attr('data-original', patchForRetina(dataOriginalURL));

            e.lazyload({effect:"fadeIn", threshold:300});
        }
    };

    var loadAvatar = function () {
        // $("img.user-avatar").each(checkLoad);
        // $("img.avatar").each(checkLoad);
        // $(window).resize();
    };
    return loadAvatar;
});

/* @source lib/date.extensions.js */;

/**
 * Returns a description of this date in relative terms.

 * Examples, where new Date().toString() == "Mon Nov 23 2009 17:36:51 GMT-0500 (EST)":
 *
 * new Date().toRelativeTime()
 * --> 'Just now'
 *
 * new Date("Nov 21, 2009").toRelativeTime()
 * --> '2 days ago'
 *
 * new Date("Nov 25, 2009").toRelativeTime()
 * --> '2 days from now'
 *
 * // One second ago
 * new Date("Nov 23 2009 17:36:50 GMT-0500 (EST)").toRelativeTime()
 * --> '1 second ago'
 *
 * toRelativeTime() takes an optional argument - a configuration object.
 * It can have the following properties:
 * - now - Date object that defines "now" for the purpose of conversion.
 *         By default, current date & time is used (i.e. new Date())
 * - nowThreshold - Threshold in milliseconds which is considered "Just now"
 *                  for times in the past or "Right now" for now or the immediate future
 * - smartDays - If enabled, dates within a week of now will use Today/Yesterday/Tomorrow
 *               or weekdays along with time, e.g. "Thursday at 15:10:34"
 *               rather than "4 days ago" or "Tomorrow at 20:12:01"
 *               instead of "1 day from now"
 *
 * If a single number is given as argument, it is interpreted as nowThreshold:
 *
 * // One second ago, now setting a now_threshold to 5 seconds
 * new Date("Nov 23 2009 17:36:50 GMT-0500 (EST)").toRelativeTime(5000)
 * --> 'Just now'
 *
 * // One second in the future, now setting a now_threshold to 5 seconds
 * new Date("Nov 23 2009 17:36:52 GMT-0500 (EST)").toRelativeTime(5000)
 * --> 'Right now'
 *
 */
var TRANSLATIONS = {
    'Right now':'现在',
    'Just now':'刚刚',
    'from now':'之后',
    'ago':'前',
    'Today':'今天',
    'Yesterday':'昨天',
    'Tomorrow':'明天',
    ' at ':'',
    's':'',
    ' ':'',
    'millisecond':'毫秒',
    'second':'秒',
    'minute':'分钟',
    'hour':'小时',
    'day':'天',
    'month':'个月',
    'year':'年',
    'Sunday':'星期天',
    'Monday':'星期六',
    'Tuesday':'星期二',
    'Wednesday':'星期三',
    'Thursday':'星期四',
    'Friday':'星期五',
    'Saturday':'星期六'
},
_t = function (key) {return TRANSLATIONS[key];};

 Date.prototype.toRelativeTime = (function() {

  var _ = function(options) {
    var opts = processOptions(options);

    var now = opts.now || new Date();
    var delta = now - this;
    var future = (delta <= 0);
    delta = Math.abs(delta);

    // special cases controlled by options
    if (delta <= opts.nowThreshold) {
      return future ? _t('Right now') : _t('Just now');
    }
    if (opts.smartDays && delta <= 6 * MS_IN_DAY) {
      return toSmartDays(this, now);
    }

    var units = null;
    for (var key in CONVERSIONS) {
      if (delta < CONVERSIONS[key])
        break;
      units = _t(key); // keeps track of the selected key over the iteration
     delta = delta / CONVERSIONS[key];
    }

    // pluralize a unit when the difference is greater than 1.
    delta = Math.floor(delta);
    if (delta !== 1) { units += _t("s"); }
    return [delta, units, future ? _t("from now") : _t("ago")].join(_t(" "));
  };

  var processOptions = function(arg) {
    if (!arg) arg = 0;
    if (typeof arg === 'string') {
      arg = parseInt(arg, 10);
    }
    if (typeof arg === 'number') {
      if (isNaN(arg)) arg = 0;
      return {nowThreshold: arg};
    }
    return arg;
  };

  var toSmartDays = function(date, now) {
    var day;
    var weekday = date.getDay(),
        dayDiff = weekday - now.getDay();
    if (dayDiff == 0)       day = _t('Today');
    else if (dayDiff == -1) day = _t('Yesterday');
    else if (dayDiff == 1 && date > now)  day = _t('Tomorrow');
    else                    day = WEEKDAYS[weekday];
    return day + _t(" at ") + date.toLocaleTimeString();
  };

  var CONVERSIONS = {
    millisecond: 1, // ms    -> ms
    second: 1000,   // ms    -> sec
    minute: 60,     // sec   -> min
    hour:   60,     // min   -> hour
    day:    24,     // hour  -> day
    month:  30,     // day   -> month (roughly)
    year:   12      // month -> year
  };
  var MS_IN_DAY = (CONVERSIONS.millisecond * CONVERSIONS.second * CONVERSIONS.minute * CONVERSIONS.hour * CONVERSIONS.day);

  var WEEKDAYS = [_t('Sunday'), _t('Monday'), _t('Tuesday'), _t('Wednesday'), _t('Thursday'), _t('Friday'), _t('Saturday')];

  return _;

})();



/*
 * Wraps up a common pattern used with this plugin whereby you take a String
 * representation of a Date, and want back a date object.
 */
Date.fromString = function(str) {
  return new Date(Date.parse(str));
};

/* autogeneration */
define("lib/date.extensions", [], function(){});

/* @source mod/relative_date.js */;

define('mod/relative_date', [
  "jquery",
  "lib/date.extensions"
], function($) {
    var updateRelativeDate = function () {
        $('.js-relative-date').each(
            function (i, el) {
                var el = $(el);
                var t = (el.attr('datetime') || el.attr('data-time')).split(/[- : + T]/);
                var d = new Date(t[0], t[1]-1, t[2], t[3], t[4], t[5]);
                !isNaN(d.getTime()) && el.html(d.toRelativeTime({nowThreshold:60*1000}));
            });
    };
        return updateRelativeDate;
    });

/* @source mod/ajax_load.js */;

define('mod/ajax_load', [
  "jquery",
  "mod/count",
  "mod/relative_date",
  "mod/user_avatar"
], function($, countDict, updateRelativeDate, loadAvatar) {
    var ajaxLoad = function(url, number_type) {
        var maxShown = 35;
        $.ajax({type: "GET",
                url: url,
                dataType: "json",
                beforeSend: function() {
                    $('.timeline .loader').show();
                },
                success: function(data) {
                    var result = data.result;
                    var length = data.length;

                    $('.timeline>ul').append(result);
                    $('.timeline .loader').hide();
                    if (length < maxShown) {
                        $('.timeline .pagination').hide();
                    } else {
                      countDict[number_type] += maxShown;
                    }
                    updateRelativeDate();
                    loadAvatar();
                }
        });
    };

    return ajaxLoad;
});

/* @source mod/userfeed_pagination.js */;

define('mod/userfeed_pagination', [
  "jquery",
  "mod/ajax_load",
  "mod/count"
], function($, ajaxLoad, countDict) {
    $(function () {
        $('.timeline .loader').hide();
        $('.timeline .pagination').show().click(
            function () {
                var number_type = "userfeed_num";
                var url = "/j/more/userfeed/" + countDict.userfeed_num;
                ajaxLoad(url, number_type);
        });
    })
});


/* @source mod/newsfeed.js */;

define('mod/newsfeed', [
  "jquery",
  "mod/user_avatar"
], function($, loadAvatar) {
    $(function () {
        $('.timeline').delegate('.expand-rest', 'click', function(){
            var last = $(this).parents('.expand-last');
            last.prevUntil('.expand-first').show(300);
            last.hide();
            loadAvatar();
        });
     });
});


/* @source mod/badge_info.js */;

define('mod/badge_info', [
  "jquery",
  "jquery-lazyload",
  "bootstrap",
  "mustache"
], function($, _, Mustache) {

    $(function() {
        $("img.badgeInfo").lazyload();
        $(".badgeInfo").each(function(){
            var options = {
                title: $(this).attr('data-title'),
                content: $(this).attr('data-reason')
            };
            $(this).popover(options);
        });
    });

});

/* @source mod/user_profile_card.js */;

define('mod/user_profile_card', [
  "jquery",
  "jquery-tmpl"
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

/* @source  */;

require(['jquery'
, 'bootbox'
, 'mod/user_profile_card'
, 'mod/badge_info'
, 'mod/newsfeed'
, 'mod/userfeed_pagination'], function($){
    //put your home code here.
});
