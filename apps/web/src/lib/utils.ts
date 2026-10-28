import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a priority score (0-100) into a display label */
export function priorityLabel(score: number): string {
  if (score >= 80) return "Critical";
  if (score >= 60) return "High";
  if (score >= 40) return "Medium";
  return "Low";
}

/** Get priority color class */
export function priorityColor(score: number): string {
  if (score >= 80) return "text-red-700 bg-red-50 border-red-200";
  if (score >= 60) return "text-orange-700 bg-orange-50 border-orange-200";
  if (score >= 40) return "text-amber-700 bg-amber-50 border-amber-200";
  return "text-green-700 bg-green-50 border-green-200";
}

/** Get status badge color */
export function statusColor(status: string): string {
  const map: Record<string, string> = {
    Received: "bg-blue-100 text-blue-800 border-blue-200",
    "Under Process": "bg-amber-100 text-amber-800 border-amber-200",
    Transferred: "bg-purple-100 text-purple-800 border-purple-200",
    Escalated: "bg-red-100 text-red-800 border-red-200",
    Disposed: "bg-green-100 text-green-800 border-green-200",
    Reopened: "bg-pink-100 text-pink-800 border-pink-200",
  };
  return map[status] ?? "bg-gray-100 text-gray-800 border-gray-200";
}

/** Get criticality color */
export function criticalityColor(code: string): string {
  const map: Record<string, string> = {
    C1: "bg-red-100 text-red-800 border-red-300",
    C2: "bg-orange-100 text-orange-800 border-orange-300",
    C3: "bg-yellow-100 text-yellow-800 border-yellow-300",
    C4: "bg-green-100 text-green-800 border-green-300",
  };
  return map[code] ?? "bg-gray-100 text-gray-800";
}

/** Format date to Indian locale */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

/** Format relative time */
export function timeAgo(date: string | Date): string {
  const now = new Date();
  const d = new Date(date);
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/** Clamp number between min and max */
export function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}
