// Toggle between real API client and mock API based on Vite env var VITE_USE_MOCK
// Export both a default export and a named `api` export so existing import styles work.
import realApiDefault, * as realApiNamed from "./api";
import mockApiDefault, * as mockApiNamed from "./mockApi";

const useMock = import.meta.env.VITE_USE_MOCK === "true";

const selectedDefault = useMock
  ? mockApiDefault ?? mockApiNamed
  : realApiDefault ?? realApiNamed;
const selectedNamed = useMock ? mockApiNamed : realApiNamed;

// Default export (for `import api from '../services'`)
export default selectedDefault;

// Named export (for `import { api } from '../services'`)
// Many files expect a named `api` binding, so provide it for compatibility by
// attaching the default under the `api` name when needed.
export const api =
  (selectedNamed && (selectedNamed as any).api) || selectedDefault;

// Re-export everything from the chosen implementation for convenience
export * from "./api"; // keep static types available; mock will be compatible at runtime
