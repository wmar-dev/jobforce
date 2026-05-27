"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "HQ", icon: "🏛️", color: "text-red-400", description: "Command Center" },
  { href: "/jobs", label: "Scout", icon: "🔭", color: "text-emerald-400", description: "Job Discovery" },
  { href: "/oracle", label: "Oracle", icon: "🔮", color: "text-violet-400", description: "Job Ranking" },
  { href: "/forge", label: "Forge", icon: "⚒️", color: "text-amber-400", description: "Resume Tailoring" },
  { href: "/coach", label: "Coach", icon: "🎯", color: "text-blue-400", description: "Interview Prep" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col py-6 px-3 shrink-0">
      <div className="mb-8 px-2">
        <div className="text-xl font-black tracking-tight text-white">⚡ JOBFORCE</div>
        <div className="text-xs text-gray-500 mt-1">Superhero Job Hunt</div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800/50"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              <div>
                <div className={`text-sm font-semibold ${isActive ? item.color : ""}`}>
                  {item.label}
                </div>
                <div className="text-xs text-gray-500">{item.description}</div>
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto px-2 pt-4 border-t border-gray-800">
        <div className="text-xs text-gray-600">Jobforce v0.1.0</div>
      </div>
    </aside>
  );
}
