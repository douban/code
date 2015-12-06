<%def name="tip()">
<%
from vilya.models.tips import Tips
text, url = Tips.get_tip()
%>
% if user.settings.show_tips:
<div class="alert alert-info hidden-phone">
<strong>tips:</strong> ${text|n}
% if url:
<a href="${url}">Try it</a>
% endif
</div>
% endif
</%def>
