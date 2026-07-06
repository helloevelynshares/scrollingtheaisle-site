import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../../styles.css";
import "./lab.css";
import { FamilyTrackerLabApp } from "./FamilyTrackerLabApp";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(
    <StrictMode>
      <FamilyTrackerLabApp />
    </StrictMode>,
  );
}
