// Script populated options boxes with option based upon user selections
$(document).ready(function(){

    // Listner for change in make, populates model select box with options
    $("#make").change(function(){

        // Get selected make
        let make = $("#make").val();

        // Clear list, add blank option and set blank option as selected
        $("#model").empty().append("<option selected value='none'>Select Model</option>");

        // Get models for selected make and add as options to select box
        if (make != "none")
        {
            let parameters = {"make":make};
            $.getJSON("/get_models", parameters, function(data, textStatus, jqXHR){
                let len = data.length;
                for (i = 0; i < len; i++)
                {
                    $('#model').append($('<option>', {value:data[i], text:data[i]}));
                }
            });
        }
    });

    // If purchase year option box is available (not available on all pages), limit purchase year to model year upon selection of model year
    if ($("#purchase_year").length != 0)
    {
        $("#model_year").change(function(){

            // Clear options and replace instruction to select year
            $("#purchase_year").empty().append("<option selected value='none'>Select Year of Purchase</option>");

            let year = (new Date()).getFullYear();
            let limit = $("#model_year").val();
            if (limit != "none")
            {
                for (i = 0; year-i >= limit; i++)
                {
                    $("#purchase_year").append($('<option>', {value:year-i, text:year-i}));
                }
            }
        });
    }
});