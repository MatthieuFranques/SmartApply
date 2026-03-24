FROM node:20-slim

WORKDIR /app

COPY package*.json ./
# Le flag --legacy-peer-deps aide parfois si tu as des conflits de versions
RUN npm install --quiet

COPY . .

EXPOSE 4200

CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--poll", "2000"]