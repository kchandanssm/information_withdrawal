(function() {
    $(".item_add").click(function() {
        $(this).parent().animate({ backgroundColor: "olive" }, "slow");
        
        return false;
    });
})(jQuery);
