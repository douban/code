require(
  ['jquery'
  , 'bootbox'
  , 'mod/newsfeed'
  , 'mod/teamfeed_pagination'
  , 'mod/issue_tag'
  , 'mod/team_header'],
  function($){

            // FIXME: 单纯用 css :hover 搞不定吗？
            $('.my_projects li').hover(
                function () {$(this).addClass('hover');},
                function () {$(this).removeClass('hover');}
            );

            var delProj = function (proj, team, onSuccess) {
                bootbox.confirm("Are you sure?", function(confirmed) {
                    if (confirmed) {
                        $.post('/hub/team/' + team + '/remove_project', {"project_name": proj}, function (ret) {
                            if (ret.r === 0) {
                                onSuccess();
                            }
                        }, 'json');
                    }
                });
            };
            $('.my_projects li .delete-btn').click(function () {
                var delBtn = $(this), proj = delBtn.attr('data-proj'), team = delBtn.attr('data-team');
                delProj(proj, team, function () { delBtn.closest('li').remove(); });
            });

  });
