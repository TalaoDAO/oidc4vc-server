$(document).ready(function() {
    $("#sending_button").click(function() {
 //     $(this).prop("disabled", true);
      $(this).html(
        `<span class="spinner-border spinner-border-sm" ></span> Sending...`
      );
    });
});
