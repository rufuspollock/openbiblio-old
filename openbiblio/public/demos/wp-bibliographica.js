/********************************************************
 * Bibliographica Wikipedia Gadget
 * meant for interaction and information exchange between 
 * Bibliographica.org and Wikipedia 
 *
 *
 * - to install you need to be a registered user of the wikipedia project.
 *  
 * - go to http://en.wikipedia.org/wiki/Special:MyPage/vector.js and write:
 *	importScript('User:Acracia/wp-biblio.js');
 *   - if you are a member of another language wikipedia, 
 *   		you can still link to this file: 
 *   	
 *   	importScriptURI('http://en.wikipedia.org/wiki/User:Acracia/wp-biblio.js');
 *
 *   	(notice the URI!!)
 *
 * - You need to reload the cache of the page for the changes to take effect: 
 * 	usually Ctrl+Shift+R will do.
 * - For an example, visit http://en.wikipedia.org/wiki/Charles_Dickens
 *   In the left sidebar there should be a box with links to the 
 *   bibliographica.org records present in both Bibliographica and 
 *   the article.
 *
 *
 *   OKFN - http://okfn.org http://bibliographica.org
 *
 ******************************************************/

$ = jQuery



function getdata (ISBN) {
  // gets data from books metioned in references and 
  // creates a list with them in the left toolbar 
  $.getJSON('http://bibliographica.org/isbn/'+ISBN, function(data) {
    // if the record is on our database, render a link to it:
    if (data != '' ) {
      $("#Bibliographica > ul").append('\n<li class="body"><a href="'+data[0].uri+'">'+data[0].title+'</a> </li>');
    } else {
    // here we will have some fancy importing scripts soon 
    // $("#Bibliographica > ul").append('<li class="body"><a href="">import work onto Blibliographica</a> </li>');
    };
  });
};


$(document).ready(function($) {
  //if we have found any links with class mw-magiclink-isbn, we add a bar to the Wikipedia sidebar for Bibliographica
    if ($("a.mw-magiclink-isbn") != '' ) { 
      $("#p-interaction").after('<div id="Bibliographica" class="portal expanded">\n\t<h5>Bibliographica</h5>\n<ul>\n</ul>\n</div>');
      $("a.mw-magiclink-isbn").each(function () {
        // render a box around the ISBN, parses the actual number from the text
        $(this).css("border", "2px dotted blue"); //so we mark the ISBN we are actually importing
        var ISBN = $(this).text().split(' ')[1] ; //scraping of the ISBN number
        // gets the info from http://bibliographica.org/isbn	
        getdata (ISBN);
        });
    };
});
