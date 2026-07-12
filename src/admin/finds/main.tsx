import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../../../styles.css";
import { AdminFindsApp } from "./AdminFindsApp";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <AdminFindsApp />
    </StrictMode>,
  );
}
