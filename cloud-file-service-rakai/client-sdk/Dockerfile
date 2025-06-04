# Use an official Node.js image as the base
FROM node:14

# Set the working directory to /app
WORKDIR /app

# Copy the package*.json files to the working directory
COPY package*.json ./
COPY tsconfig.json ./

# Install the dependencies
RUN npm install

# Copy the application code to the working directory
COPY . .

# Build the client-sdk
RUN npm run build

# Expose the port
EXPOSE 8080

# Run the command to start the development server
CMD ["npm", "start"]