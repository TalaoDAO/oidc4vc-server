$(document).ready(function() {
    $("#in_progress_button").click(function() {
//      $(this).prop("disabled", true);

      try {if (document.forms['form']['checkValidity']()) {
        $(this).html(
          `<span class="spinner-border spinner-border-sm" ></span> Déploiement en cours......`
        );
      }} catch(error){
        $(this).html(
          `<span class="spinner-border spinner-border-sm" ></span> Déploiement en cours...`
        );
      }


    });
});
