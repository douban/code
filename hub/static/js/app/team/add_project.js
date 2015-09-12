require([
        'jquery',
        'mod/drop_down_list'
], function($, drop_down_list){
    var addProjectForm = $('#add-project-form');
    var success = function (data) {
        addProjectForm.submit();
    };

    // search for repos
    var reqUrl = '/api/autocomplete_repos';
    var templ = $('#templ-repos-autocomplete');

    $('#project_id').focusin(function(){
        var inputObj = $(this);
        drop_down_list(inputObj, success, 'dd', reqUrl, templ, "repos", '');
    });
});
