"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Building2, 
  FileText, 
  LayoutDashboard, 
  Bot, 
  BookOpen, 
  ShieldCheck 
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Overview", href: "/", icon: Building2 },
    { name: "Submit Grievance", href: "/complaints", icon: FileText },
    { name: "Admin Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Municipal Assistant", href: "/assistant", icon: Bot },
    { name: "Knowledge Base", href: "/knowledge-base", icon: BookOpen },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200 shadow-sm">
      {/* Top Academic Disclaimer Banner */}
      <div className="bg-slate-900 text-slate-300 text-xs py-1.5 px-4 text-center font-medium flex items-center justify-center gap-2">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        <span>Academic Project: 100% Non-ML Deterministic NLP & Classical Information Retrieval System (Zero External Cloud APIs)</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-indigo-600 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight block">
                SmartCity Grievance
              </span>
              <span className="text-[11px] font-semibold text-blue-600 uppercase tracking-wider block -mt-1">
                Municipal Redressal
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="flex items-center gap-1 sm:gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700 font-semibold"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
