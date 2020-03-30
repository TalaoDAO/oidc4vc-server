server {
    listen      80;
    server_name 192.168.0.34;
    location / {
        proxy_pass         "http://localhost:5000";
        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        fastcgi_read_timeout 300s;
        proxy_read_timeout 300;
    }
    location /static {
        alias  /opt/deployment/my-api-app/static/;
    }
    error_log  /var/log/nginx/api-error.log;
    access_log /var/log/nginx/api-access.log;
}



