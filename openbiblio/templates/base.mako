<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
   <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
   <title>${self.title()}</title>
   <link rel="shortcut icon" href="http://m.okfn.org/gfx/logo/favicon.ico" type="image/x-icon" />
   <link rel="stylesheet" href="http://m.okfn.org/kforge/css/master.css" type="text/css" media="screen, print" title="Master stylesheet" charset="utf-8" />
   <link rel="stylesheet" href="http://ckan.net/css/ckan.master.css" type="text/css" media="screen, print" />
   <%def name="headlinks()"></%def>
   ${self.headlinks()}
 </head>
<body>
<style>
  #warnings {
	color: red;
	margin-left: 100px;
  }
</style>
<div id="top">
  <h1>
      <a href="http://bibliographica.org/">Bibliographica<sup style="font-size:0.4em;">Beta</sup></a>
  </h1>
  <%def name="navlinks()"></%def>
  <div id="navlinks" style="float:right;">
  ${self.navlinks()}
  </div>
</div>
<div id="content">
${self.body()}
</div>
<div id="footer">
  <p>
    <a href="http://validator.w3.org/check/referer" title="Valid XHTML 1.1">XHTML</a>
    | <a href="http://jigsaw.w3.org/css-validator/check/referer">CSS</a>
    | <a href="http://www.okfn.org/ckan/">Project Home Page</a>

    | <a href="http://www.okfn.org/contact/">Contact Us</a>
    | <a href="http://www.okfn.org/privacy-policy/">Privacy Policy</a>
  </p>
  <p>
    <img style="margin-bottom: -5px;" src="http://m.okfn.org/images/logo/okf_logo_white_and_green_tiny.png" alt="Open Knowledge Foundation" /> An <a href="http://www.okfn.org/">Open Knowledge Foundation</a> Project
  </p>

  <p>
    v0.11a
    | (c) Open Knowledge Foundation
    | All material available under an <a href="/license">open license</a>
    | <a href="http://www.opendefinition.org/1.0/"><img style="border: none; margin-bottom: -4px;" src="http://m.okfn.org/images/ok_buttons/ok_90x15_blue.png" alt="This Content and Data is Open" /></a>
  </p>
</div><!-- /footer -->
</body>
</html>
