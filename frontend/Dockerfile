# Stage 1: Build the Next.js application
FROM node:18-alpine AS builder

# Install build dependencies required by native packages like 'sharp'
RUN apk add --no-cache build-base gcc autoconf automake zlib-dev libpng-dev nasm bash vips-dev

# Set working directory
WORKDIR /app

# Copy package.json and lock file
COPY package*.json ./
COPY pnpm-lock.yaml ./
COPY .npmrc ./

# Install dependencies using pnpm
RUN npm install -g pnpm
RUN pnpm install

# Copy the rest of the application source code
COPY . .

# Build the Next.js application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.21-alpine

# Copy built assets from the builder stage
COPY --from=builder /app/public /usr/share/nginx/html
COPY --from=builder /app/.next /usr/share/nginx/html/.next

# Copy Nginx configuration
# We will need to create this nginx.conf file next
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 