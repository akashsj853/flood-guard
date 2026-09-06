# FloodGuard AI — frontend image
# Build with Vite, then serve the static bundle with a tiny Nginx server that
# proxies /api to the backend container.
FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Proxy API calls to the backend service (docker-compose overrides API_TARGET).
ENV API_TARGET=http://backend:8000
RUN apk add --no-cache envsubst

COPY nginx.conf.template /etc/nginx/nginx.conf.template
EXPOSE 80
CMD ["/bin/sh", "-c", "envsubst '$$API_TARGET' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
