docker exec -u 0 erp-dev-frontend-1 "/usr/share/nginx/html/assets && ls" && docker exec -t -u 0 erp-dev-frontend-1 cp -R /usr/share/nginx/html/nextassets/* /usr/share/nginx/html/assets

