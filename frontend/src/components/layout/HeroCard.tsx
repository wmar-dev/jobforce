"use client";

interface HeroCardProps {
  codename: string;
  name: string;
  power: string;
  colorClass: string;
  icon: string;
}

export function HeroCard({ codename, name, power, colorClass, icon }: HeroCardProps) {
  return (
    <div className={`rounded-lg border p-3 ${colorClass} bg-opacity-10 border-opacity-30`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="font-bold text-sm">{codename}</span>
      </div>
      <div className="text-xs text-gray-400">{name}</div>
      <div className="text-xs text-gray-500 mt-1">{power}</div>
    </div>
  );
}
