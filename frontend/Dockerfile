# Stage 1: build the Vue SPA (Node 22, same major used locally).
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve the static build with nginx on port 3000, the origin the
# backend CORS already accepts. The API base is read at runtime from the
# API_BASE env var, rewritten into /config.js before nginx starts.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD sh -c 'sed -i "s|http://localhost:8000|${API_BASE:-http://localhost:8000}|g" /usr/share/nginx/html/config.js && nginx -g "daemon off;"'
