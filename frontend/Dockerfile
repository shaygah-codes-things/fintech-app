# build
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Vite reads env at build time; set default API base to http://localhost:8000
ENV VITE_API_BASE=http://localhost:8000
RUN npm run build

# serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# basic gzip & caching can be added with a custom nginx.conf if you like
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
