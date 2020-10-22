$(document).ready(function() {
    $("#loading_button").click(function() {
 //     $(this).prop("disabled", true);

      try {if (document.forms['form']['checkValidity']()) {
        $(this).html(
          `<span class="spinner-border spinner-border-sm" ></span> Loading...`
        );
      }} catch(error){
        $(this).html(
          `<span class="spinner-border spinner-border-sm" ></span> Loading...`
        );
      }
    });
});
