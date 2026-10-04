"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Building2, 
  FileText, 
  LayoutDashboard, 
  Bot, 
  BookOpen, 
  ShieldCheck,
  User,
  LogOut,
  LogIn,
  UserPlus,
  FolderOpen
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, isCitizen, isAdmin, isSuperAdmin, logout } = useAuth();

  // Dynamic Navigation Items based on authentication role
  let navItems = [
    { name: "Overview", href: "/", icon: Building2 },
    { name: "Submit Grievance", href: "/complaints", icon: FileText },
    { name: "Municipal Assistant", href: "/assistant", icon: Bot },
  ];

  if (isAuthenticated) {
    if (isCitizen) {
      navItems = [
        { name: "My Complaints", href: "/complaints/my", icon: FolderOpen },
        { name: "Submit Grievance", href: "/complaints", icon: FileText },
        { name: "Municipal Assistant", href: "/assistant", icon: Bot },
      ];
    } else if (isAdmin) {
      navItems = [
        { name: "Admin Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "Lodge Intake", href: "/complaints", icon: FileText },
        { name: "Municipal Assistant", href: "/assistant", icon: Bot },
      ];
      // Knowledge base is strictly restricted to Super Administrator
      if (isSuperAdmin) {
        navItems.push({ name: "Knowledge Base", href: "/knowledge-base", icon: BookOpen });
      }
    }
  }

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
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
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

          {/* Auth Controls & Profile Pill */}
          <div className="flex items-center gap-2">
            {isAuthenticated ? (
              <div className="flex items-center gap-2.5">
                {/* User Info Badge */}
                <div className={`hidden md:flex items-center gap-2 px-3 py-1 rounded-xl border text-xs ${
                  isAdmin 
                    ? "bg-indigo-50 border-indigo-200 text-indigo-900" 
                    : "bg-blue-50 border-blue-200 text-blue-900"
                }`}>
                  {isAdmin ? (
                    <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                  ) : (
                    <User className="w-3.5 h-3.5 text-blue-600" />
                  )}
                  <div className="text-left">
                    <span className="font-bold block leading-tight">{user?.full_name}</span>
                    <span className="text-[10px] text-slate-500 block leading-tight">
                      {isSuperAdmin ? "Super Admin" : isAdmin ? `Admin: ${user?.department || "Dept"}` : "Citizen"}
                    </span>
                  </div>
                </div>

                {/* Logout Button */}
                <button
                  onClick={logout}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold text-xs transition-all shadow-sm"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5 text-slate-500" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold text-xs transition-all"
                >
                  <LogIn className="w-3.5 h-3.5 text-slate-500" />
                  <span>Sign In</span>
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-sm shadow-blue-500/20 transition-all"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Register</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
