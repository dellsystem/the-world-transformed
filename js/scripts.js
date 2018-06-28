$('.ui.accordion').accordion();
$('.ui.embed').embed();
$('.section').scrollie({
    scrollingInView: function(element) {
        var background = element.data('background');
        $('#sidebar').css('background-color', background);
        var elementId = element[0].id;
        $('#header .active.item').removeClass('active');
        $('#anchor-' + elementId).addClass('active');
    }
});
