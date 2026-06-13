# 🎨 Xephy-AI Trading Dashboard

This is the front-end user interface for the Xephy-AI Trading System. It is a highly responsive, modern, and dark-themed web dashboard built to monitor quantitative trading activity, live PnL, and signal histories.

## 🛠 Tech Stack

- **Framework:** [React 18](https://react.dev/)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Styling:** [TailwindCSS 3](https://tailwindcss.com/)
- **Icons:** [Lucide React](https://lucide.dev/)
- **API Client:** Axios (connected via a modular API service layer)

## 📁 Directory Structure

```text
src/
├── assets/         # Static images, SVGs, and CSS entry points
├── components/     # Reusable React components
│   └── layout/     # Sidebar, Header, and Layout wrapper
├── pages/          # Main application views
│   ├── Dashboard.jsx  # Main live trading view (Live PnL, Signals, Overview)
│   └── Trades.jsx     # Historical completed trades with profit/loss
├── services/       # External integrations
│   └── api.js      # Centralized Axios API calls to the Flask backend
├── App.jsx         # React Router and main application root
└── main.jsx        # React DOM entry point
```

## 🔄 State Management & Polling

Because the Xephy-AI backend operates as an independent engine taking trades continuously, this frontend does not rely on complex Redux states. Instead, it uses a highly efficient **React Hook Polling** architecture.

On the `Dashboard.jsx` and `Trades.jsx` pages, `useEffect` hooks automatically poll the backend `/api/positions` and `/api/trades` endpoints every 2-5 seconds. This guarantees that your UI is always perfectly in sync with the backend Engine's memory, displaying floating PnL and newly closed trades instantly.

## 🚀 Running the Project

First, ensure you have NodeJS installed.

1. **Install Dependencies:**
   ```bash
   npm install
   ```

2. **Start Development Server:**
   ```bash
   npm run dev
   ```
   *The server will start on `http://localhost:5173`.*

3. **Build for Production:**
   ```bash
   npm run build
   ```
   *This compiles the React code into static HTML/JS/CSS inside the `/dist` directory, ready to be served by Nginx, Apache, or even Flask.*

## 🔗 Connecting to the Backend

The frontend defaults to looking for the backend Flask server at `http://localhost:5000/api`. If your backend is hosted elsewhere (e.g., a VPS or cloud provider), update the `API_BASE_URL` inside `src/services/api.js`.
