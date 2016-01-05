
require.config({ enable_ozma: true });


/* @source  */;

require(['jquery-tmpl'], function(){

    var increment = 10; //badge_item per page / Additional badges displayed per click
    var index = 0; //Number of times more badge info has been requested
    var badge_list;
    var item_count;
    var last_day = null;

    $(function get_badges() {
        $.getJSON("/badge/badges", function(badges) {
                badge_list = badges;
                get_item_count();
        });
    });

    var get_item_count = function() {
        $.getJSON("/badge/count", {}, function(count) {
                item_count = count[0];
                populate_list();
                if (increment < item_count) {
                    $(".timeline .more").append("<a class='more_items' href='javascript:void(0)'>See more</a>");
                    $("a.more_items").click(populate_list);
                }
        });
    };

    var populate_list = function() {
        index++;
        var data_vars = {
                ind: index - 1,
                inc: increment
        };
        $.getJSON("/badge/items", data_vars, function(items) {
            $.each(items, function(i, day) {
                var badge_date = new Date(day[0][3]);
                var text = "";
                if (last_day == null || last_day.toDateString() != badge_date.toDateString()) {
                    var date_string = badge_date.getFullYear() + "-" + (badge_date.getMonth()+1) + "-" + badge_date.getDate();
                    text += "<h2>" + date_string + " </h2>";
                }
                last_day = badge_date;
                text += "<dl><div class='action'></div></dl>";
                $(".timeline>dl").append(text);
                var data = [];
                $.each(day, function(j, item) {
                    var id = item[0];
                    var item_date = new Date(item[3]);
                    item_date.setHours(item_date.getHours() + item_date.getTimezoneOffset()/60);
                    var time_string = item_date.toLocaleTimeString();
                    var item_data = {
                        badge_id: id,
                        recipient: item[1],
                        avatar: item[4],
                        reason: item[2] == null ? "" : item[2],
                        item_time: time_string.substring(0, time_string.length - 3),
                        badge_name: badge_list[id-1][1],
                        summary: badge_list[id-1][2]
                    };
                    data.push(item_data);
                });
                $("#timeline_template").tmpl(data).appendTo(".action:last");
            });
            if (index * increment > item_count) {
                $(".more_items").remove();
            }
        });
    };

});
