$(function() {
    var options = {
        autoOpen: false,
        resizable: true,
        draggable: true,
        modal: true,
        width: 1000,
        maxHeight: 350,
        position: {
            my: "left top",
            at: "center",
            of: window
        },
        show: {
            effect: "blind",
            duration: 1000
        },
        hide: {
            effect: "explode", 
            duration: 1000
        }
    };

    $( ".dialog" ).dialog(options);
    $( ".opener" ).on( "click", function() {
        $( "#story-" + this.id) .dialog( "option","position",{my: "left top", at: "left bottom", of: $("#"+this.id)} );
        $( "#story-" + this.id) .dialog( "open" ).prev().css('background','#d9edf7').css('color','#31708f');
        return false;
    });
});
