<%def name="fetch_new()">

<div class="modal hide" id="badgeModal">
    <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal">×</button>
    <h3>恭喜您获得徽章</h3>
    </div>
    <div class="modal-body">
    <p>恭喜您获得了: {{#badges}} {{{imgurl}}} {{/badges}}</p>
    </div>
    <div class="modal-footer">
    % if request.user:
    <a href="/people/${request.user.username}" class="btn">去看看</a>
    % endif
    </div>
</div>

</%def>
