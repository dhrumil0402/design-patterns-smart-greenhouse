import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import DashboardPage from "./pages/DashboardPage";

function HomePage() {
  return (
    <div>
      <h2 className="mb-2 text-2xl font-semibold">Welcome</h2>
      <p className="text-gray-600">
        Smart Greenhouse control panel. Head to the dashboard to see the
        current placeholder sections — they will be filled in over the
        coming phases.
      </p>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
    </Routes>
  );
}
