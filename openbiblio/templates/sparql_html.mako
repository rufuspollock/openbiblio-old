<%inherit file="/base.mako" />

<%def name="title()">SPARQL Endpoint</%def>

<%def name="body()">
<% 
	from openbiblio.utils import render_html
%>
  <form method="get" action=""><div>
  <textarea name="query" cols="80" rows="15">
${c.query}
  </textarea><br />
  <input type="submit" value="Run Query" />
  </div></form>

% if c.warnings:
<div id="warnings">
  <ul>
% for warning in c.warnings:
    <li>${warning}</li>
% endfor
  </ul>
</div>
% endif

% if c.bindings:
  <table width="100%" border="1">
    <tr>
% for b in c.bindings:
      <th>${b}</th>
% endfor
    </tr>
% for row in c.results:
    <tr>
% for b in c.bindings:
      <td>${render_html(row[b])|n}</td>
% endfor
    </tr>
% endfor
  </table>
% endif
</%def>
