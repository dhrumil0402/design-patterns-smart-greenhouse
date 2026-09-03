import { Link, Outlet } from "react-router-dom";
import HealthStatus from "./HealthStatus";

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold">Smart Greenhouse</h1>
            <nav className="mt-1 flex gap-4 text-sm text-gray-600">
              <Link to="/" className="hover:text-gray-900">
                Home
              </Link>
              <Link to="/dashboard" className="hover:text-gray-900">
                Dashboard
              </Link>
            </nav>
          </div>
          <HealthStatus />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
