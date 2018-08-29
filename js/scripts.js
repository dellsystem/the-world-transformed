// If we're on the programme page, hide sessions from a different day
$('#programme-menu .item').click(function (e) {
    // this is extremely ugly but it works lol
    var day = this.innerText;
    $('#programme-menu .active').removeClass('active');
    $(this).addClass('active');
    $('#programme tr').hide();
    $('#programme tr').filter(function () {
        return $(this).data('day') === day;
    }).show();
});
$('.ui.accordion').accordion();
$('.ui.embed').embed();
$('.section').scrollie({
    View: function(element) {
        var background = element.data('background');
        $('#sidebar').css('background-color', background);
        var elementId = element[0].id;
        $('#header .active.item').removeClass('active');
        $('#anchor-' + elementId).addClass('active');
    }
});
$('#hamburger').click(function (element) {
    $('#mobile-menu').toggle();
    $('#header').toggleClass('expanded');
});
$('#mobile-menu .anchor').click(function (e) {
    // Terrible hack to simulate closing the menu
    $('#hamburger').click();
    // Smooth scrolling but only if already on the homepage
    var aid = $(this).attr("href").substring(1);
    if ($(aid).length) {
        e.preventDefault();
        $('html,body').animate({scrollTop: $(aid).offset().top}, 'slow');
    }
});
// sorry lmao, no time to do this properly
$('#desktop-menu .anchor').click(function (e) {
    // Smooth scrolling but only if already on the homepage
    var aid = $(this).attr("href").substring(1);
    if ($(aid).length) {
        e.preventDefault();
        $('html,body').animate({scrollTop: $(aid).offset().top}, 'slow');
    }
})
