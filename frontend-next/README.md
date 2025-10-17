# MCP Bets - Frontend (Next.js)This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).



AI-Powered Betting Intelligence Platform## Getting Started



## 🚀 Quick StartFirst, run the development server:



```bash```bash

# Install dependenciesnpm run dev

npm install# or

yarn dev

# Run development server# or

npm run devpnpm dev

# or

# Build for productionbun dev

npm run build```



# Start production serverOpen [http://localhost:3000](http://localhost:3000) with your browser to see the result.

npm start

```You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.



Visit [http://localhost:3000](http://localhost:3000)This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.



## 📋 Prerequisites## Learn More



- Node.js 18+ To learn more about Next.js, take a look at the following resources:

- npm or yarn

- Python backend running on port 8000- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.

- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

## 🔧 Environment Setup

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

Create `.env.local`:

## Deploy on Vercel

```bash

NEXT_PUBLIC_AUTH0_DOMAIN=your-domain.auth0.comThe easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

NEXT_PUBLIC_AUTH0_CLIENT_ID=your-client-id

NEXT_PUBLIC_API_URL=http://localhost:8000Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

```

## 🏗️ Project Structure

```
frontend-next/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── globals.css        # Global styles
│   └── api/               # API routes
│       └── openai/
│           └── route.ts   # Proxy to FastAPI
├── components/            # React components
│   ├── AuthProvider.tsx   # Auth0 wrapper
│   └── CustomLogin.tsx    # Login modal
├── types/                 # TypeScript types
│   └── auth.ts            # Auth interfaces
└── utils/                 # Utility functions
    └── auth.ts            # Auth helpers
```

## 🔐 Authentication

Custom Auth0 implementation with:
- Custom login UI (no redirects)
- Direct API authentication
- Token management with expiration
- Hybrid Auth0 SDK integration

## 🎨 Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Custom CSS**: Component-specific styles
- **Responsive Design**: Mobile-first approach

## 📡 API Integration

Next.js API routes proxy requests to FastAPI backend:

```typescript
// Frontend makes request to Next.js API
fetch('/api/openai', { 
  method: 'POST',
  body: JSON.stringify({ prompt: '...' })
})

// Next.js proxies to FastAPI
// localhost:3000/api/openai → localhost:8000/api/openai
```

## 🧪 Development

```bash
# Start dev server with turbopack
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🚢 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Manual Deployment
```bash
# Build
npm run build

# Start production server
npm start
```

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Auth0 React SDK](https://auth0.com/docs/libraries/auth0-react)
- [Tailwind CSS](https://tailwindcss.com/docs)

## 🤝 Contributing

See main project README for contribution guidelines.

## 📄 License

See main project LICENSE file.
