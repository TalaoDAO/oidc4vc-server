$(document).ready(function() {
    $("#in_progress_button").click(function() {
//      $(this).prop("disabled", true);
      $(this).html(
        `<span class="spinner-border spinner-border-sm" ></span> In progress...`
      );
    });
});
