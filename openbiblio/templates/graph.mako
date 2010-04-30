<%inherit file="/base.mako" />
<%def name="title()">Comprehensive Knowledge Archive Network</%def>

<%def name="headlinks()">
<%
	from openbiblio.utils import rdf_getstr
%>
  <link rel="meta" title="RDF" type="application/rdf+xml" href="${rdf_getstr(request)}" />
</%def>

<%def name="navlinks()">
<%
	from openbiblio.utils import rdf_getstr
%>
<a href="${rdf_getstr(request)}" title="RDF Resource Description Framework">
  <img border="0" src="http://www.w3.org/RDF/icons/rdf_w3c_button.32"
   alt="RDF Resource Description Framework Icon"/>
</a>
</%def>

<%def name="body()">
<%
	from openbiblio.utils import render_html
%>
% if c.warnings:
<div id="warnings">
  <ul>
% for warning in c.warnings:
    <li>${warning}</li>
% endfor
  </ul>
</div>
% endif
<table width="100%" border="1">
% for s,p,o in c.triples:
<tr>
    <td>${render_html(s)|n}</td>
    <td>${render_html(p)|n}</td>
    <td>${render_html(o)|n}</td>
</tr>
% endfor
</table>
</%def>
