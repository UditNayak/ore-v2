import { useQuery } from "@tanstack/react-query";
import { api } from "./api/client";

interface HealthResponse {
  status: string;
  service: string;
}

/**
 * Phase 0 landing page. Confirms the frontend builds and can reach the backend
 * /health endpoint. Real pages (Feed, QuestionDetail, Dashboard) arrive in Phase 6.
 */
export default function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async (): Promise<HealthResponse> => {
      const res = await api.get<HealthResponse>("/health");
      return res.data;
    },
  });

  const backend = isLoading
    ? "checking…"
    : isError
      ? "unreachable"
      : `${data?.status} (${data?.service})`;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 text-slate-800">
      <h1 className="text-3xl font-bold">Organizational Reasoning Engine</h1>
      <p className="mt-2 text-slate-500">
        An AI that learns how experts think — not one that just searches harder.
      </p>
      <div className="mt-6 rounded-lg border border-slate-200 bg-white px-5 py-3 shadow-sm">
        <span className="font-medium">Backend:</span>{" "}
        <span className={isError ? "text-red-600" : "text-emerald-600"}>{backend}</span>
      </div>
    </div>
  );
}
