//
// KForge in jQuery. A tiny little adaptation of the "legacy" KForge 
// Prototype/Behaviour-based JS to jQuery.
//
// Depends: jQuery 1.3.2 (untested, but will probably work on any >1.2)
//
// Author: Nick Stenning, 2009
//

// jQuery.noConflict();

jQuery(function ($) {

    // Yes, I know it's ugly, but hey -- it's my "legacy" CSS -- =)
    $('.box').prepend('<span class="rtop"><span class="r1"></span><span class="r2"></span><span class="r3"></span><span class="r4"></span></span>')
             .append('<span class="rbottom"><span class="r4"></span><span class="r3"></span><span class="r2"></span><span class="r1"></span></span>');

    $.each({
      'loginform-name': '<username>',
      'loginform-password': 'password',
      'project-search-terms': 'Search terms...',
      'user-search-terms': 'Search terms...'
    }, 
    function (id, text) {
        var elem = $('#' + id);
        
        elem.bind('focus', function () {
            if (this.value === text) {
                $(this).removeClass('greyed').addClass('darkened').attr('value', '');
            };
        }).bind('blur', function () {
            if (this.value === '' || this.value === undefined) {
                $(this).removeClass('darkened').addClass('greyed').attr('value', text);
            };
        });
        
        if (elem.value === '' || elem.value === undefined) {
            $(elem).attr('value', text).addClass('greyed');
        }
    });
});
