FROM nginx:alpine

# Install Node.js and npm
RUN apk add --update nodejs npm

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy frontend files
COPY index.html .
COPY app.js .
COPY style.css .

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]