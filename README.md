# 🚀 SonqoBase

**Plataforma de base de datos efímera con capacidades de RAG (Retrieval-Augmented Generation) y búsqueda vectorial**

SonqoBase es una API REST moderna construida con FastAPI que proporciona bases de datos temporales con auto-expiración, almacenamiento vectorial, y procesamiento inteligente de documentos PDF usando embeddings de IA.

---

## ✨ Características Principales

### 🗄️ Base de Datos Efímera
- **Auto-expiración**: Las bases de datos y colecciones se eliminan automáticamente después de su tiempo de vida
- **Multi-tenant**: Cada proyecto tiene su propia base de datos aislada
- **TTL automático**: Índices TTL en MongoDB para limpieza automática

### 🤖 RAG & Búsqueda Vectorial
- **Embeddings con Google Gemini**: Generación de embeddings de alta calidad
- **Búsqueda semántica**: Búsqueda vectorial usando MongoDB Atlas Vector Search
- **Procesamiento de PDFs**: Extracción de texto, chunking inteligente, y generación de embeddings
- **Streaming de progreso**: Seguimiento en tiempo real del procesamiento de documentos

### 📄 Procesamiento de Documentos
- **Ingesta de PDFs**: Carga y procesamiento de archivos PDF
- **Chunking automático**: División inteligente de documentos en fragmentos
- **GridFS**: Almacenamiento eficiente de archivos grandes
- **Jobs asíncronos**: Procesamiento en background con seguimiento de estado

### 🔐 Seguridad & Control
- **API Keys**: Autenticación basada en claves API
- **Master Key**: Administración segura del sistema
- **Rate limiting**: Control de concurrencia por plan (Free, Starter, Pro)
- **Planes de usuario**: Sistema de planes con límites configurables

### 🎯 Event-Driven Architecture
- **Event Bus**: Arquitectura basada en eventos para procesamiento asíncrono
- **Listeners**: Procesamiento modular de eventos (PDF → Texto → Chunks → Embeddings → Storage)
- **Auditoría**: Registro automático de eventos importantes

---

## 🛠️ Stack Tecnológico

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - API REST moderna y rápida
- **Base de Datos**: [MongoDB Atlas](https://www.mongodb.com/atlas) - Base de datos NoSQL con Vector Search
- **Embeddings**: [Google Gemini](https://ai.google.dev/) - Generación de embeddings
- **PDF Processing**: pdfplumber, PyMuPDF - Extracción de texto de PDFs
- **Storage**: GridFS - Almacenamiento de archivos grandes
- **Python**: 3.11+

---

## 📦 Instalación

### Requisitos Previos
- Python 3.11 o superior
- MongoDB Atlas (cuenta gratuita disponible)
- Google API Key (para embeddings)

### 1. Clonar el repositorio
```bash
git clone https://github.com/oliveraluis/SonqoBase.git
cd SonqoBase
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:

```env
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
MONGO_META_DB=sonqo_meta
GOOGLE_API_KEY=tu_google_api_key
MASTER_KEY=tu_master_key_segura
```

### 5. Ejecutar en desarrollo
```bash
fastapi dev
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

---

## 🚀 Despliegue en Producción

Para desplegar en producción, consulta la guía completa en [DEPLOYMENT.md](DEPLOYMENT.md)

**Plataformas soportadas:**
- ✅ Railway (Recomendado)
- ✅ Render
- ✅ Fly.io
- ✅ Google Cloud Run
- ✅ AWS

### Comando de producción
```bash
fastapi run --host 0.0.0.0 --port $PORT
```

---

## 📚 Uso de la API

### 1. Crear un usuario
```bash
POST /api/v1/admin/users
Authorization: Bearer {MASTER_KEY}

{
  "email": "usuario@ejemplo.com",
  "plan": "Pro"
}
```

### 2. Crear un proyecto
```bash
POST /api/v1/projects
Authorization: Bearer {API_KEY}

{
  "name": "Mi Proyecto",
  "slug": "mi-proyecto",
  "description": "Descripción del proyecto",
  "ttl_hours": 24
}
```

### 3. Ingerir un PDF
```bash
POST /api/v1/{collection}/ingest/pdf
Authorization: Bearer {API_KEY}

Form Data:
- file: archivo.pdf
- chunk_size: 1000 (opcional)
```

### 4. Consultar con RAG
```bash
POST /api/v1/{collection}/query
Authorization: Bearer {API_KEY}

{
  "query": "¿Cuál es el contenido principal del documento?",
  "top_k": 5
}
```

### 5. Insertar documentos
```bash
POST /api/v1/{collection}
Authorization: Bearer {API_KEY}

{
  "data": {
    "nombre": "Juan",
    "edad": 30
  }
}
```

---

## 🏗️ Arquitectura

### Event-Driven Pipeline

```
PDF Upload → GridFS Storage → Text Extraction → Chunking → Embeddings → Vector Storage
     ↓            ↓                  ↓              ↓            ↓             ↓
  Job Created  Saved Event    Extracted Event  Chunked Event  Generated   Completed
```

### Componentes Principales

- **`app/api/`**: Endpoints REST
- **`app/services/`**: Lógica de negocio
- **`app/listeners/`**: Event listeners para procesamiento asíncrono
- **`app/infra/`**: Repositorios y clientes de infraestructura
- **`app/domain/`**: Entidades y eventos del dominio
- **`app/middleware/`**: Autenticación y autorización

---

## 🔧 Configuración

### Planes de Usuario

| Plan    | Concurrencia PDF | Límites           |
|---------|------------------|-------------------|
| Free    | 1                | Básico            |
| Starter | 2                | Intermedio        |
| Pro     | 5                | Avanzado          |

### TTL (Time To Live)

- **Proyectos**: Configurable por proyecto (default: 24 horas)
- **GridFS**: 24 horas automático
- **Vectores**: Heredan TTL del proyecto

---

## 📊 Monitoreo

### Jobs
```bash
GET /api/v1/jobs/{job_id}
```

Respuesta:
```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "pages_processed": 10,
    "chunks_created": 50,
    "embeddings_generated": 50
  }
}
```

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 👤 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)

---

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/) por el excelente framework
- [MongoDB](https://www.mongodb.com/) por Vector Search
- [Google Gemini](https://ai.google.dev/) por los embeddings de IA

---

## 📞 Soporte

¿Tienes preguntas o problemas? Abre un [issue](https://github.com/tu-usuario/SonqoBase/issues) en GitHub.

---

<div align="center">
  <strong>Hecho con ❤️ usando FastAPI y MongoDB</strong>
</div>
