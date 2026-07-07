import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../../../styles.css";
import { AdminStoresApp } from "./AdminStoresApp";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <AdminStoresApp />
    </StrictMode>,
  );
}
