require(
    ['jquery', 'jquery-tmpl', 'bootstrap'],
    function ($) {
        var member_query_cache = {};
        var project_query_cache = {};
        var autocomplete_member = function (query, process) {
            var $input = $('input.js-group-member')
            var group_name = $input.data('group-name');
            var team_name = $input.data('team-name');

            // if in cache use cached value, if don't wanto use cache remove this if statement
            if(member_query_cache[query]){
                process(member_query_cache[query]);
                return;
            }
            if( typeof searching != "undefined") {
                clearTimeout(searching);
                process([]);
            }
            searching = setTimeout(function() {
                return $.getJSON(
                    '/api/teams/' + team_name + '/members/',
                    { query: query },
                    function(data){
                        var new_data = [];
                        $.each(data, function(){
                            new_data.push(this.name);
                        });
                        // save result to cache, remove next line if you don't want to use cache
                        member_query_cache[query] = new_data;
                        // only search if stop typing for 300ms aka fast typers
                        return process(new_data);
                    }
                );
            }, 300); // 300 ms
        }
        var autocomplete_project = function (query, process) {
            var $input = $('input.js-group-project')
            var group_name = $input.data('group-name');
            var team_name = $input.data('team-name');

            // if in cache use cached value, if don't wanto use cache remove this if statement
            if(project_query_cache[query]){
                process(project_query_cache[query]);
                return;
            }
            if( typeof searching != "undefined") {
                clearTimeout(searching);
                process([]);
            }
            searching = setTimeout(function() {
                return $.getJSON(
                    '/api/teams/' + team_name + '/projects/',
                    { query: query },
                    function(data){
                        var new_data = [];
                        $.each(data, function(){
                            new_data.push(this.name);
                        });
                        // save result to cache, remove next line if you don't want to use cache
                        project_query_cache[query] = new_data;
                        // only search if stop typing for 300ms aka fast typers
                        return process(new_data);
                    }
                );
            }, 300); // 300 ms
        }
        $('input.js-group-member').typeahead({source: autocomplete_member});
        $('input.js-group-project').typeahead({source: autocomplete_project});
        $(".js-add-group-member").on('click', function () {
            var tmpl = $("#tmpl-group-member");
            var $input = $(this).parents().find('input.js-group-member');
            var group_id = $input.data('group');
            var team_id = $input.data('team');
            var group_name = $input.data('group-name');
            var team_name = $input.data('team-name');
            var val = $input.val()
            if (val === '' || val === undefined)
                return;
            $.ajax({
                type: 'POST',
                data: JSON.stringify({
                    'name': $input.val()
                }),
                contentType: 'application/json; charset=UTF-8',
                url: '/api/teams/' + team_name + '/groups/' + group_name + '/members/',
                dataType: 'json',
                success: function (ret) {
                    $("ul#group-members").append($.tmpl(tmpl, ret))
                }
            });
        });
        $(".js-add-group-project").on('click', function () {
            var tmpl = $("#tmpl-group-project");
            var $input = $(this).parents().find('input.js-group-project');
            var group_id = $input.data('group');
            var team_id = $input.data('team');
            var group_name = $input.data('group-name');
            var team_name = $input.data('team-name');
            var val = $input.val()
            if (val === '' || val === undefined)
                return;
            $.ajax({
                type: 'POST',
                data: JSON.stringify({
                    'name': $input.val()
                }),
                contentType: 'application/json; charset=UTF-8',
                url: '/api/teams/' + team_name + '/groups/' + group_name + '/projects/',
                dataType: 'json',
                success: function (ret) {
                    $("ul#group-projects").append($.tmpl(tmpl, ret))
                }
            });
        });
    }
);
