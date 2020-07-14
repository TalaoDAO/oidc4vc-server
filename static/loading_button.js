$(document).ready(function() {
    $("#loading_button").click(function() {
 //     $(this).prop("disabled", true);
      $(this).html(
        `<span class="spinner-border spinner-border-sm" ></span> Loading...`
      );
    });
});
