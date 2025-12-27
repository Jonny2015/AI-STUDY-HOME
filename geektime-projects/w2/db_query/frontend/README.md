# Database Query Tool - Frontend

React frontend for the Database Query Tool using Refine and Ant Design.

## Prerequisites

- Node.js 18+
- npm or pnpm or yarn

## Installation

1. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   # or
   yarn install
   ```

## Development

Run the development server:
```bash
npm run dev
# or
pnpm dev
# or
yarn dev
```

The application will be available at http://localhost:3000 (or the port shown in terminal).

## Type Checking

Run TypeScript type checker:
```bash
npm run type-check
```

## Testing

Run E2E tests with Playwright:
```bash
# First time: install Playwright browsers
npx playwright install

# Run tests
npm run test:e2e
```

## Project Structure

```
src/
├── components/      # React components
├── pages/          # Page components
├── services/       # API services
├── types/          # TypeScript type definitions
├── App.tsx         # Root component
└── main.tsx        # Entry point
```

## Tech Stack

- React 18
- TypeScript (strict mode)
- Refine 5
- Ant Design
- Tailwind CSS
- Monaco Editor
- Vite
