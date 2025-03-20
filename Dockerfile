FROM node:16  # Use the appropriate Node.js version
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5000
CMD ["node", "main.js"]