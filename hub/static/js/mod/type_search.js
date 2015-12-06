define('mod/type_search',[
    'jquery',
    'string-score',
],  function() {
    var typeSearching = false,
        projectName = $('#project_name').val(),
        currentBranch = $('#current_branch').val(),
        fileList,
        fileListContainer,
        fileListContainerBody,
        searchInput = $('<input class="typing-search-input" type="text" autocomplete="off" spellcheck="false">'),
        subPathsEle = $('#J_SubPaths'),
        FILE_PATH_PREFIX = ['', projectName, 'blob', currentBranch, ''].join('/'),
        TAG_MARK = 'mark',
        TPL_FILE_LIST_WRAP = '\
            <div class="span12">\
                <table class="tree-browser finder" cellspacing="0" cellpadding="0">\
                    <tbody>{ITEMS}</tbody>\
                </table>\
            </div>',
        TPL_FILE_LIST_ITEM = '<tr class="tree-item"><td><a href="' + FILE_PATH_PREFIX + '{URL}">{NAME}</td></tr>',
        CSS = '\
            input.typing-search-input { display:none; border:none; box-shadow:none; border-radius:none; padding:0; margin-bottom:0; font-size:100%; vertical-align:top; transition:none; }\
            input.typing-search-input:focus { box-shadow:none; }\
            .tree-browser.finder td { padding-left:20px; }\
            .tree-browser.finder tr.hover td { background:#fffeeb; }',

        SCROLLING_HOVER_LOCK = false,
        CLICK_LOCK = false,
        BLACK_LIST = { 'INPUT': 1, 'TEXTAREA': 1 };
        LOCK_TIMEOUT = 150;

    $('<style>' + CSS + '</style>').appendTo('head');

    // insert search input
    searchInput.insertAfter(subPathsEle);
    $(document)
        .keydown(function(evt) {
            if (typeSearching && evt.keyCode === 27) {
                searchInput.blur();

                evt.preventDefault();
            }
        })

        .keypress(function(evt) {
            if (typeSearching || evt.target.nodeName in BLACK_LIST ) return;

            if (!evt.metaKey && evt.charCode === 't'.charCodeAt(0)) {

                typeSearching = true;

                var def = $.Deferred();

                if (!fileList) {
                    $.get('/api/' + projectName + '/git/allfiles', {'branch': currentBranch}, function(res) {
                        fileList = res;
                        fileListContainer = $(TPL_FILE_LIST_WRAP.replace('{ITEMS}', buildFileListHtml(fileList))).appendTo('.raw');
                        fileListContainerBody = fileListContainer.find('tbody');

                        fileListContainerBody
                            .bind('mouseover mouseout', function(evt) {
                                // console.log('mouse')
                                if (SCROLLING_HOVER_LOCK) return;

                                var target = evt.target,
                                    ele;

                                if (target.nodeName === 'TR') {
                                    ele = $(target);
                                } else {
                                    ele = $(target).parents('tr');
                                }

                                if (ele) {
                                    $(this).find('tr').removeClass('hover');

                                    if (evt.type === 'mouseover') {
                                        ele.addClass('hover');
                                    } else {
                                        ele.removeClass('hover');
                                    }
                                }

                            })

                            .click(function(evt) {
                                var target = evt.target;

                                if (target.nodeName !== 'A') {
                                    window.location = $(target).find('a').attr('href');
                                }

                                CLICK_LOCK = true;
                            });

                        def.resolve();
                    }, 'json');
                } else {
                    def.resolve();
                }

                def.done(function() {
                    searchInput.focus();
                });

                evt.preventDefault();
            }
        });

    searchInput
        .focus(function(evt) {
            $(this).show();

            subPathsEle.hide();

            fileListContainerBody.html(buildFileListHtml(fileList));
            fileListContainer.show();
            $('#tree').hide();
            $('#readme').hide();
        })

        .blur(function(evt) {
            var self = this;

            setTimeout(function() {
                if (CLICK_LOCK) return;

                $(self).hide().val('');

                subPathsEle.show();

                fileListContainer && fileListContainer.hide();
                $('#tree').show();
                $('#readme').show();

                typeSearching = false;
            }, LOCK_TIMEOUT);
        })

        .keydown(function(evt) {
            var keyCode, item;

            if ((keyCode = evt.keyCode) === 27 || !typeSearching || !fileList) {
                return;
            }

            switch (keyCode) {
                // UP
                case 38:
                    fileSelect(-1);
                    evt.preventDefault();
                    return;
                // DOWN
                case 40:
                    fileSelect(1);
                    evt.preventDefault();
                    return;
                // ENTER
                case 13:
                    item = fileListContainerBody.find('tr.hover');
                    item.click();
                    return;
            }

            var ele = this;

            setTimeout(function() {
                var value = $.trim(ele.value),
                    result;

                if (!value) {
                    result = fileList;
                } else {
                    // match
                    result = matchFileList(fileList, value);

                    // sort
                    result = sortFileList(result);

                    // get final fileList
                    result = $.map(result, function(item) {
                        return item.file;
                    });

                }

                // fileListContainerBody.html(buildFileListHtml(result));
                fileListContainerBody[0].innerHTML = buildFileListHtml(result, value);

            }, 0);

            evt.stopPropagation();
        });

    function buildFileListHtml(fileList, keyword) {
        var html = '';

        fileList.forEach(function(fileName) {
            var name = fileName;
            if (keyword) {
                name = name.replace(keyword, '<' + TAG_MARK + '>' + keyword + '</' + TAG_MARK + '>');
            }
            html += TPL_FILE_LIST_ITEM.replace(/\{URL\}/g, fileName).replace(/\{NAME\}/g, name);
        });

        return html;
    }

    function matchFileList(fileList, keyword) {
        var result = [];

        fileList.forEach(function(file) {
            var score;
            if (score = file.score(keyword)) {
                result.push({
                    score: score,
                    file: file
                });
            }
        });

        return result;
    }

    function sortFileList(fileListWithScore) {
        return fileListWithScore.sort(function(a, b) {
            return b.score - a.score;
        });
    }

    function fileSelect(direction) {
        var currentFileItem = fileListContainerBody.find('tr.hover'),
            fileItems, fileItem;

        if (currentFileItem.length === 0) {
            fileItems = fileListContainerBody.find('tr');
            fileItem = direction === 1 ? fileItems.eq(0) : fileItems.eq(-1);
        } else {
            fileItem = direction === 1 ? currentFileItem.next() : currentFileItem.prev();

            if (fileItem.length === 0) {
                fileItems = fileListContainerBody.find('tr');
                // scroll loop
                fileItem = direction === 1 ? fileItems.eq(0) : fileItems.eq(-1);
            }
        }

        currentFileItem.removeClass('hover');
        fileItem.addClass('hover');

        scrollIntoView(fileItem);
    }

    var lockTimer;

    function scrollIntoView(element) {
        element = $(element);

        var offsetTop = element.offset().top,
            scrollTop = $(document).scrollTop(),
            viewPortHeight = $(window).height(),
            diff;

        if ( (diff = offsetTop - scrollTop) <= 0 ||
                (diff = offsetTop + element.height() - (scrollTop + viewPortHeight)) >= 0 ) {

            window.scrollTo(0, scrollTop + diff);

            // prevent scrolling trigger mouse event
            // console.log('lock')
            SCROLLING_HOVER_LOCK = true;

            if (lockTimer) {
                clearTimeout(lockTimer);
                lockTimer = null;
            }

            lockTimer = setTimeout(function() {
                // console.log('unlock')
                SCROLLING_HOVER_LOCK = false;
            }, LOCK_TIMEOUT);
        }

    }

});
