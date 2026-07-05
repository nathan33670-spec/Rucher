# ─── Étape 1 : build statique de la SPA Vue/Vuetify ──────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ─── Étape 2 : service des fichiers statiques via nginx ──────────
FROM nginx:alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
# Garantit que nginx (utilisateur non-root) peut lire tous les fichiers, quelles
# que soient les permissions héritées du contexte de build (extraction tar, etc.).
RUN chmod -R a+rX /usr/share/nginx/html
EXPOSE 80
