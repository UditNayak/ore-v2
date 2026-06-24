import { BrowserRouter, Route, Routes } from "react-router-dom";
import Nav from "./components/Nav";
import AskPage from "./pages/AskPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 text-slate-800">
        <Nav />
        <Routes>
          <Route path="/" element={<AskPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
