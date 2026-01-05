# Trading Setup Detector

Sistema de deteccion de patrones chartistas en criptomonedas usando Claude Vision.

## Funcionalidades

- **Subir Patrones**: Sube una imagen de un setup chartista y Claude Vision lo analiza
- **Monitoreo**: Monitorea criptomonedas de Binance en multiples timeframes
- **Deteccion Automatica**: Escanea cada 5 minutos buscando patrones similares
- **Alertas Multicanal**: Dashboard, Telegram y Email

## Stack Tecnologico

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **AI**: Anthropic Claude Vision API
- **Datos**: Binance API

## Requisitos

- Python 3.10+
- Node.js 18+
- API Key de Anthropic

## Instalacion

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuracion
cp .env.example .env

# Editar .env con tu API key de Anthropic
# ANTHROPIC_API_KEY=tu-api-key

# Iniciar servidor
uvicorn src.main:app --reload
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Copiar configuracion
cp .env.local.example .env.local

# Iniciar servidor de desarrollo
npm run dev
```

## Uso

1. Accede a http://localhost:3000
2. Registra una cuenta
3. **Patterns**: Sube imagenes de patrones chartistas que quieras detectar
4. **Analyze**: Claude Vision analizara el patron y extraera caracteristicas
5. **Watchlist**: Agrega las criptomonedas que quieres monitorear
6. **Scanner**: Inicia el scanner para buscar patrones automaticamente
7. **Settings**: Configura alertas de Telegram y Email

## API Endpoints

- `POST /api/v1/auth/register` - Registro
- `POST /api/v1/auth/login` - Login
- `GET/POST /api/v1/patterns` - CRUD de patrones
- `POST /api/v1/patterns/{id}/analyze` - Analizar patron con Claude
- `GET/POST /api/v1/watchlist` - CRUD de watchlist
- `POST /api/v1/scanner/scan-now` - Escaneo manual
- `POST /api/v1/scanner/start` - Iniciar scanner automatico
- `GET /api/v1/alerts` - Historial de alertas

## Consideraciones de Costos

El uso de Claude Vision tiene costos por llamada a la API:
- Cada comparacion de patron usa ~4,500 tokens
- Recomendado empezar con pocas cryptos y 1 patron para testing
- Usar escaneo manual en lugar de automatico durante desarrollo

## Estructura del Proyecto

```
trading-setup-detector/
├── backend/
│   ├── src/
│   │   ├── auth/          # Autenticacion JWT
│   │   ├── patterns/      # CRUD patrones + analisis Claude
│   │   ├── watchlist/     # Gestion de cryptos
│   │   ├── scanner/       # Logica de escaneo
│   │   ├── alerts/        # Telegram, Email, Dashboard
│   │   ├── binance/       # Cliente Binance API
│   │   └── claude/        # Cliente Claude Vision
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── lib/           # API client, utilities
│   │   └── types/         # TypeScript types
│   └── package.json
│
└── README.md
```

## Licencia

MIT
