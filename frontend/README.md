# Personal Analytics - Frontend

This is the frontend for the Personal Analytics MVP. It's built with modern web technologies to provide a fast, responsive, and beautiful user experience.

## Technologies Used

- **React 19**
- **TypeScript**
- **Vite**
- **Tailwind CSS** (for styling and glassmorphism UI)
- **React Router** (for routing and protected routes)
- **Recharts** (for data visualization)
- **Axios** (for API communication)
- **Lucide React** (for icons)

## Setup and Running

1. Ensure you have Node.js 16+ installed.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `frontend` root directory if your backend runs on a different port:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Open your browser to `http://localhost:5173`.

## Architecture

- `src/components/Login.tsx`: Handles Google and GitHub OAuth login flows.
- `src/components/Dashboard.tsx`: Main dashboard with insights, charts, and data tables.
- `src/context/AuthContext.tsx`: Manages the JWT token and user profile globally.
- `src/App.tsx`: Sets up React Router and protected routes.

Please see the root `README.md` for full stack setup and configuration instructions.
