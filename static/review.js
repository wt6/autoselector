// Script populated options boxes with option based upon user selections
$(document).ready(function(){

    // Listner for change in make, populates model select box with options
    $("input[name=own]").change(function(){

        // If car is owned show maintenance input box else hide
        if ($(this).val() == 'yes'){
            $("#maintenance").show();
        }
        else{
            $("#maintenance").hide();
        }
    });
});