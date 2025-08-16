

```yaml
x-api: &api
  # image: ghcr.io/ptronico/rinha25:latest
  build:
    # context: ./../../../rinha25
    context: ./../../../rinha25-starlette
    target: dev
  command: uvicorn src:app --host 0.0.0.0 --port 8000 --no-access-log --workers 1 --loop uvloop --http httptools # --log-level error
  # command: uvicorn src:app --host 0.0.0.0 --port 8000 --no-access-log --workers 1 --loop uvloop --http httptools
  environment:
    - APP_PORT=8000
    - PROCESSOR_DEFAULT_URL=http://payment-processor-default:8080
    - PROCESSOR_FALLBACK_URL=http://payment-processor-fallback:8080
    - SEMNUM=1
  networks:
    - backend
    - payment-processor
  ports:
    - "9999:8000"
  deploy:
    resources:
      limits:
        cpus: "1.5"
        memory: "350MB"
  # develop:
  #   watch:
  #     - action: sync
  #       path: ../../../rinha25
  #       target: /app
  #       ignore:
  #         - .venv/
  #     - action: rebuild
  #       path: ./uv.lock

services:
  # nginx:
  #   image: nginx:1.29-alpine
  #   container_name: rinha-nginx
  #   volumes:
  #     - ./nginx.conf:/etc/nginx/nginx.conf:ro
  #   depends_on:
  #     - api1
  #     - api2
  #   ports:
  #     - "9999:9999"
  #   networks:
  #     - backend
  #     - payment-processor
  #   deploy:
  #     resources:
  #       limits:
  #         cpus: "0.3"
  #         memory: "100MB"
  #   sysctls:
  #     net.core.somaxconn: 65535
  #     net.ipv4.tcp_max_syn_backlog: 65535
  api1:
    <<: *api
    hostname: api1
  # api2:
  #   <<: *api
  #   hostname: api2
networks:
  backend:
    driver: bridge
  payment-processor:
    external: true
```


```
worker_processes auto;
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    access_log off;
    error_log /dev/null crit;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    keepalive_timeout 30;
    keepalive_requests 100000;

    client_max_body_size 0;

    upstream api {
        server api1:8000; # max_fails=1 fail_timeout=1s;
        server api2:8000; # max_fails=1 fail_timeout=1s;
        # server api3:8000 max_fails=1 fail_timeout=1s;
        # server api4:8000 max_fails=1 fail_timeout=1s;
        # server unix:/shared/backend1.sock;
        # server unix:/shared/backend2.sock;
        keepalive 100;
    }

    server {
        listen 9999 default_server;

        location / {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
    }
}
```
