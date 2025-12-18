import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { BrowserRouter } from "react-router-dom";
import * as serviceWorkerRegistration from "./serviceWorkerRegistration";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

// Register service worker for PWA offline capability
// Disabled in development to avoid reload loops
if (process.env.NODE_ENV === 'production') {
  serviceWorkerRegistration.register({
    onSuccess: (registration) => {
      console.log('[PWA] Service worker registered successfully:', registration);
    },
    onUpdate: (registration) => {
      console.log('[PWA] New content available; please refresh.');
    }
  });
} else {
  console.log('[DEV] Service worker disabled in development mode');
} // Deploy 20251218-112908
