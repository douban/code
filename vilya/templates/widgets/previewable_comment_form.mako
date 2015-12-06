<%def name="previewable_comment_form(project, title=None, description='', class_='', zen=True)">
<div class="comment-form previewable-comment-form write-selected ${class_}">
	%if title is not None:
		<input type="text" name="title" tabindex="3" class="title required valid" value="${title}" placeholder='Title' required>
	%endif
	<p class="help">Comments are parsed with <a href="http://daringfireball.net/projects/markdown/syntax" target="_blank">Markdown</a></p>
	<ul class="edit-preview-tabs tabs js-preview-tabs nav">
		<li class="active"><a href="#write_bucket" data-toggle="tab" class="write-tab" action="write">Write</a></li>
		<li><a href="#preview_bucket" data-toggle="tab" class="preview-tab" action="preview">Preview</a></li>
	</ul>

	<div class="tab-content">
    <div id="write_bucket" class="tab-pane active write-content ${'zen-enabled' if zen else ''}">
      % if zen:
        <a href="#" class="go-zen enable-fullscreen hide-phone" original-title="Zen Mode" title="Zen Mode">
            <span class="mini-icon mini-icon-fullscreen"></span>
        </a>
      % endif
			<textarea name="body" id="pull_body" class="js-comment-field" tabindex="4" data-suggester-list="pull_body_mentions" >${description}</textarea>
		</div>
		<div id="preview_bucket" class="tab-pane preview-content">
			<div class="content-body markdown-body" data-api-url="/preview?repository=${project.id}">
				<p>Loading preview...</p>
			</div>
		</div>
	</div>
</div>

</%def>
