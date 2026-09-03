const sections = [
  { id: "section-overview", title: "Overview" },
  { id: "section-sensors", title: "Sensors" },
  { id: "section-controls", title: "Controls" },
  { id: "section-automation", title: "Automation" },
  { id: "section-configuration", title: "Configuration" },
  { id: "section-events", title: "Events" },
];

export default function DashboardPage() {
  return (
    <div>
      <h2 className="mb-6 text-2xl font-semibold">Dashboard</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sections.map((section) => (
          <section
            key={section.id}
            id={section.id}
            className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
          >
            <h3 className="mb-2 text-base font-medium">{section.title}</h3>
            <p className="text-sm text-gray-500">Coming in a later phase.</p>
          </section>
        ))}
      </div>
    </div>
  );
}
