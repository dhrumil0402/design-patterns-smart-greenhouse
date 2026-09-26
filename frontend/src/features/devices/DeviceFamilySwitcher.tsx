import type { DeviceFamily } from "../../services/api";

interface Props {
  selected: DeviceFamily;
  onSelect: (family: DeviceFamily) => void;
  disabled?: boolean;
}

export default function DeviceFamilySwitcher({ selected, onSelect, disabled }: Props) {
  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={() => onSelect("simulation")}
        disabled={disabled}
        className={`rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50 ${
          selected === "simulation"
            ? "bg-emerald-600 text-white"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        Simulation
      </button>
      <button
        type="button"
        onClick={() => onSelect("edge")}
        disabled={disabled}
        className={`rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50 ${
          selected === "edge"
            ? "bg-emerald-600 text-white"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        Edge
      </button>
    </div>
  );
}