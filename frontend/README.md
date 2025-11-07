# Oracle NL-SQL Frontend

**Tier 3: React-based web UI for managing the Oracle NL-SQL MCP Server**

## Features

- **Dashboard**: Overview of databases, patterns, and statistics
- **File Upload**: Drag-and-drop PowerBuilder file upload
- **Pattern Management**: View and manage learned SQL patterns
- **Database Management**: Connect and explore databases
- **Real-time Monitoring**: Track learning progress and jobs

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

Visit: http://localhost:3000

### 3. Build for Production
```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── NavBar.tsx
│   │   ├── StatsCard.tsx
│   │   ├── FileUploadZone.tsx
│   │   └── PatternTable.tsx
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Upload.tsx
│   │   ├── Patterns.tsx
│   │   ├── Databases.tsx
│   │   └── Logs.tsx
│   ├── services/           # API clients
│   │   └── api.ts
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   ├── App.tsx             # Main app component
│   └── main.tsx            # Entry point
├── public/                 # Static assets
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool (fast HMR)
- **Material-UI (MUI)** - Component library
- **React Router** - Routing
- **Axios** - HTTP client
- **React Dropzone** - File upload
- **Recharts** - Charts and visualizations

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`:

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',  // Proxied to http://localhost:8000/api/v1
});

export const searchMetadata = (question: string) => {
  return api.post('/metadata/search', { question });
};
```

Vite proxy configuration handles CORS automatically.

## Pages

### 1. Dashboard (`/`)
- System health status
- Learning statistics
- Recent patterns
- Quick actions

### 2. Upload (`/upload`)
- PowerBuilder file upload (drag-and-drop)
- CSV metadata upload
- Job status monitoring
- Upload history

### 3. Patterns (`/patterns`)
- Learned SQL patterns table
- Search and filter
- View pattern details
- Delete patterns

### 4. Databases (`/databases`)
- Connected databases list
- Schema explorer
- Connection management
- Metadata migration

### 5. Logs (`/logs`)
- Real-time backend logs
- Filter by level (info, warn, error)
- Search logs
- Export logs

## Development

### Run Linter
```bash
npm run lint
```

### Type Checking
```bash
npx tsc --noEmit
```

### Environment Variables
Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

## Deployment

### Option 1: Static Hosting
```bash
npm run build
# Deploy dist/ folder to Netlify, Vercel, etc.
```

### Option 2: Docker
```bash
docker build -t oracle-nlsql-frontend .
docker run -p 3000:3000 oracle-nlsql-frontend
```

### Option 3: Docker Compose
```bash
# From project root
docker-compose up
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### API Connection Errors
```
Error: Network Error

Solution:
1. Check backend is running: http://localhost:8000/api/health
2. Check CORS configuration in backend
3. Check Vite proxy configuration
```

### Build Errors
```
Error: Module not found

Solution:
rm -rf node_modules package-lock.json
npm install
```

## Contributing

1. Create feature branch
2. Make changes
3. Run linter: `npm run lint`
4. Test locally
5. Submit PR

---

**Version**: 2.0.0
**React**: 18.2.0
**Last Updated**: 2025-11-07
