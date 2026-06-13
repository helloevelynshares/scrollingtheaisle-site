import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../../../styles.css";
import { AdminSuggestionsApp } from "./AdminSuggestionsApp";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <AdminSuggestionsApp />
    </StrictMode>,
  );
}
