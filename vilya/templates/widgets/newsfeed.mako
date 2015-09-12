	<div class="timeline">
		<dl>
			%for day, events_ in groupby(events, key=lambda etuple: format_date(etuple[1].date)):
				<h2>${day}: ${day == today and _("Today") or day == yesterday and _("Yesterday") or None}</h2>
				<dl>
					%for proj, event, context_ in events_:
					<dt class="${event.kind}">
						<a href="${event.render('url', context_)}">
							<span class="time">${format_time(event.date, '%H:%M')}</span>
							${event.render('title', context_)}
							%if event.author:
								by <span class="author">${format_author(event.author)}</span>
							%endif
							on ${proj.name}
						</a>
					</dt>
					<dd class="${event.kind}">
						${event.render('description', context_)}
					</dd>
					%endfor
				</dl>
			%endfor
		</dl>
	</div>
