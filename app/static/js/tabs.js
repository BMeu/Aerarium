/**
 * Functionality used for tabs.
 */

// Show the tab given in the URL after loading the document.
$(document).ready(function() {
    let url = document.location.toString();
    if (url.match('#')) {
        let anchor = url.split('#')[1];
        $('.nav-tabs a[href="#' + anchor + '"]').tab('show');
    }
});

// Update the anchor in the URL whenever a tab is selected.
$(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function(event) {
    window.location.hash = event.target.hash;
});
