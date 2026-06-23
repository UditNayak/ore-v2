import axios from "axios";

// API base URL is injected at build/run time; defaults to localhost for bare dev.
const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL });
