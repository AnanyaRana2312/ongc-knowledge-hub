// src/constants.js
// Shared constants for the ONGC Knowledge Hub frontend.

export const DOMAINS = [
  { value: "all", label: "🔍 All Domains (Cross-Search)" },
  { value: "safety", label: "🦺 Safety" },
  { value: "drilling", label: "⛏️ Drilling" },
  { value: "HR management", label: "👥 HR Management" },
  { value: "supply chain management", label: "🔗 Supply Chain Management" },
  { value: "fire", label: "🔥 Fire" },
  { value: "procurement", label: "📋 Procurement" },
  { value: "production", label: "🏭 Production" },
  { value: "geology", label: "🌍 Geology" },
  { value: "finance and accounts", label: "💰 Finance and Accounts" },
  { value: "materials managements", label: "📦 Materials Management" },
  { value: "health and safety", label: "🏥 Health and Safety" },
  { value: "instrumentation", label: "🔧 Instrumentation" },
];

export const INGEST_DOMAINS = DOMAINS.filter((d) => d.value !== "all");

export const SAMPLE_QUESTIONS = [
  "What is the procedure for an oil spill emergency?",
  "Explain the drilling safety protocols",
  "What are the HR leave policies?",
  "Describe the procurement process for equipment",
];
