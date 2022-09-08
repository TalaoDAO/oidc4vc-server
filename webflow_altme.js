
  $altme = jQuery;
  
  $altme(document).ready(function () {

  logout();    

    if(!localStorage.getItem('testObject'))
    {
      const el1 = document.getElementById("logoutbutton");
        el1.style.visibility= 'hidden' ;
       const el2 = document.getElementById("signinbutton");
        el2.style.visibility = 'visible' ;
      } 
      else         
      {
        const el1 = document.getElementById("logoutbutton");
        el1.style.visibility= 'visible' ;
      const el2 = document.getElementById("signinbutton");
        el2.style.visibility = 'hidden' ;
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
