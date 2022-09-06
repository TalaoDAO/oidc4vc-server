


  $altme = jQuery;
  
    $altme(document).ready(function () {
	
	  logout();    

      if(!localStorage.getItem('testObject'))
      {
        const el1 = document.getElementById("logoutbutton");
					el1.remove();
        } 
        else         
        {
        const el2 = document.getElementById("signinbutton");
					el2.remove();
        }   
             
    });

  
  function logout()
  {
    //fuction for logout
     $altme(document).on("click",'#logoutbutton',function(){
       localStorage.removeItem("testObject");
       localStorage.removeItem("group");
     });
  }


