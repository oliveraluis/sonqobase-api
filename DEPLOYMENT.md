# 🚀 Guía de Despliegue - SonqoBase API

## 📋 Requisitos Previos

- Cuenta en [Railway.app](https://railway.app) o [Render.com](https://render.com)
- MongoDB Atlas configurado
- Google API Key para embeddings

---

## 🎯 Opción 1: Desplegar en Railway (Recomendado)

### Paso 1: Preparar el repositorio
```bash
git add .
git commit -m "feat: prepare for production deployment"
git push origin develop
```

### Paso 2: Crear proyecto en Railway
1. Ve a [railway.app](https://railway.app)
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Autoriza Railway a acceder a tu repositorio
5. Selecciona el repositorio `ephemeral-db-api`

### Paso 3: Configurar Variables de Entorno
En el dashboard de Railway, ve a **Variables** y agrega:

```env
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
MONGO_META_DB=sonqo_meta
GOOGLE_API_KEY=tu_google_api_key_aqui
MASTER_KEY=tu_master_key_segura
PORT=8000
```

### Paso 4: Desplegar
Railway detectará automáticamente el `railway.json` y `Procfile`, y desplegará tu aplicación.

**✅ Tu API estará disponible en:** `https://tu-proyecto.up.railway.app`

---

## 🎯 Opción 2: Desplegar en Render

### Paso 1: Crear Web Service
1. Ve a [render.com](https://render.com)
2. Click en **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub
4. Selecciona `ephemeral-db-api`

### Paso 2: Configuración
- **Name:** `sonqobase-api`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `fastapi run --host 0.0.0.0 --port $PORT`

### Paso 3: Variables de Entorno
Agrega las mismas variables que en Railway.

### Paso 4: Desplegar
Click en **"Create Web Service"**

**✅ Tu API estará disponible en:** `https://sonqobase-api.onrender.com`

---

## 🎯 Opción 3: Desplegar en Fly.io

### Paso 1: Instalar Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Verificar instalación
fly version
```

### Paso 2: Login y crear app
```bash
fly auth login
fly launch
```

Sigue las instrucciones interactivas:
- **App name:** `sonqobase-api`
- **Region:** Selecciona la más cercana
- **PostgreSQL:** No (usamos MongoDB Atlas)
- **Redis:** No

### Paso 3: Configurar secrets
```bash
fly secrets set MONGO_URI="mongodb+srv://..."
fly secrets set MONGO_META_DB="sonqo_meta"
fly secrets set GOOGLE_API_KEY="tu_key"
fly secrets set MASTER_KEY="tu_master_key"
```

### Paso 4: Desplegar
```bash
fly deploy
```

**✅ Tu API estará disponible en:** `https://sonqobase-api.fly.dev`

---

## 🔧 Verificar Despliegue

Una vez desplegado, verifica que todo funcione:

```bash
# Health check
curl https://tu-dominio.com/

# Documentación
https://tu-dominio.com/docs
```

---

## 📊 Monitoreo

### Railway
- Dashboard: Logs en tiempo real
- Métricas: CPU, RAM, Network

### Render
- Logs: En el dashboard del servicio
- Métricas: Disponibles en el plan pago

### Fly.io
```bash
# Ver logs
fly logs

# Ver métricas
fly status
```

---

## 🔐 Seguridad en Producción

### ✅ Checklist:
- [ ] Variables de entorno configuradas (no hardcodeadas)
- [ ] `MASTER_KEY` segura y única
- [ ] MongoDB Atlas con IP whitelist configurada
- [ ] CORS configurado correctamente
- [ ] Rate limiting habilitado
- [ ] HTTPS habilitado (automático en Railway/Render/Fly)

---

## 🐛 Troubleshooting

### Error: "Application failed to start"
- Verifica que todas las variables de entorno estén configuradas
- Revisa los logs: `fly logs` o en el dashboard de Railway/Render

### Error: "Cannot connect to MongoDB"
- Verifica que `MONGO_URI` sea correcta
- Asegúrate de que Railway/Render IP esté en la whitelist de MongoDB Atlas (usa `0.0.0.0/0` para permitir todas)

### Error: "Port already in use"
- Asegúrate de usar `$PORT` en el comando de inicio
- Railway/Render asignan el puerto automáticamente

---

## 📚 Recursos

- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## 🎉 ¡Listo!

Tu API de SonqoBase está ahora en producción. Comparte tu URL con tu equipo y empieza a usarla.

**URL de documentación:** `https://tu-dominio.com/docs`
