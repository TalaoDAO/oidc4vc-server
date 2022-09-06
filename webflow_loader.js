//To handle javascript being disabled on browsers, this will auto redirect to a page with customizable message to enable javascript for proper functionality.


  $mo = jQuery;
   
    $mo(document).ready(function () {

      //logout function loaded, invoked on click.
	       
      if(!localStorage.getItem('testObject'))//insert loader only when the session does not exist
      {
        $mo('body').css('display','none');
      }
    
      setTimeout(function(){
      
            var url = window.location.href;
            var token = url.split("?id_token=")[1];
        if ( window.location.origin == "https://thierry-webflow.webflow.io") 
        { 
            if (token) 
            {
                var check = parseJwt(token);
                localStorage.setItem('testObject', JSON.stringify(check));
                var getStorageValue = localStorage.getItem('testObject');
                var str = JSON.parse(getStorageValue);
                var group = str.group;
                redirect(group);
            }
         else if (localStorage.getItem('testObject') == null) 
         {
       window.location.href = "https://talao.co/sandbox/op/authorize?client_id=uuheppwxbc&response_type=id_token&redirect_uri=https://thierry-webflow.webflow.io/loader"; 
            }   
    }
        
             }, 10);      
    });

    function redirect(group) {
    if(group == 'Default')
       {
         window.location.replace('https://thierry-webflow.webflow.io/');
       }
       else if (group == 'Test')
      {
         window.location.replace('https://'+window.location.host+'/test');
	  }
       else window.location.replace('https://' + window.location.host);
    }

    function parseJwt(token) {
        var header = token.split('.')[0];
        var header_base64 = header.replace(/-/g, '+').replace(/_/g, '/');
        var jsonHeader = decodeURIComponent(atob(header_base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        var payload = token.split('.')[1];
        var payload_base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
        var jsonPayload = decodeURIComponent(atob(payload_base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        var headerJsonObj = JSON.parse(jsonHeader);
        var payloadJsonObj = JSON.parse(jsonPayload);
        var userGroup = payloadJsonObj.group;
    	
        localStorage.setItem('group', JSON.stringify(userGroup));
      
        return Object.assign({}, headerJsonObj, payloadJsonObj);
    };
  
  

