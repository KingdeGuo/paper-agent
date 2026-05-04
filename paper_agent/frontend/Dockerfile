# Frontend Dockerfile — multi-stage build with nginx

# Build stage
FROM node:25-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY public/ public/
COPY src/ src/

RUN npm run build

# Runtime stage
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
