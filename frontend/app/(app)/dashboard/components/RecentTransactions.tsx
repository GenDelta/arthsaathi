"use client";

import { useEffect, useState, useCallback } from "react";
import { SurfaceCard } from "@/components/ui/SurfaceCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  ArrowUpRight,
  ArrowDownRight,
  Inbox,
  Trash2,
  ChevronDown,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import {
  transactionsApi,
  type Transaction,
  type TransactionFilters,
} from "@/lib/api-client";

// ─── Helpers ───────────────────────────────────────────────────────────────────

function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) throw new Error("invalid");
    return new Intl.DateTimeFormat("en-IN", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    // Raw bank date string (e.g. "30-Sep-\n2026") — clean it and return as-is
    return iso.replace(/\s+/g, " ").trim();
  }
}

// ─── Skeleton ──────────────────────────────────────────────────────────────────

function SkeletonRow() {
  return (
    <div className="flex items-center justify-between p-5 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-white/10" />
        <div className="flex flex-col gap-2">
          <div className="h-3.5 w-32 bg-white/10 rounded" />
          <div className="h-2.5 w-20 bg-white/10 rounded" />
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <div className="h-3.5 w-16 bg-white/10 rounded" />
        <div className="h-4 w-20 bg-white/10 rounded-full" />
      </div>
    </div>
  );
}

// ─── Filter Bar ────────────────────────────────────────────────────────────────

const TYPE_OPTIONS = [
  { value: "all", label: "All Types" },
  { value: "INCOME", label: "Income" },
  { value: "EXPENSE", label: "Expense" },
] as const;

type TypeFilter = "all" | "INCOME" | "EXPENSE";


function SelectPill({
  value,
  options,
  onChange,
}: {
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          appearance-none
          bg-[#111] border border-white/10 text-text-primary text-sm
          pl-3 pr-8 py-1.5 rounded-lg
          focus:outline-none focus:border-amber-400/60
          cursor-pointer hover:border-white/20 transition-colors
        "
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={12}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none"
      />
    </div>
  );
}

// ─── Empty State ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center px-6">
      <div className="p-4 rounded-full bg-white/5">
        <Inbox size={32} className="text-text-secondary" />
      </div>
      <p className="text-text-primary font-medium">No transactions found</p>
      <p className="text-text-secondary text-sm max-w-xs">
        Upload a bank statement PDF or log an entry via voice above to get
        started.
      </p>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────

interface RecentTransactionsProps {
  refresh?: number;
  start_date?: string;
  end_date?: string;
}

export function RecentTransactions({ refresh = 0, start_date, end_date }: RecentTransactionsProps) {
  const { accessToken } = useAuthStore();

  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Reset to page 1 whenever filters change
  useEffect(() => { setPage(1); }, [typeFilter, start_date, end_date, refresh]);

  const fetchTransactions = useCallback(() => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);

    const filters: TransactionFilters = {
      type: typeFilter,
      page,
      page_size: PAGE_SIZE,
      ...(start_date ? { start_date } : {}),
      ...(end_date ? { end_date } : {}),
    };

    transactionsApi
      .list(accessToken, filters)
      .then((res) => {
        setTransactions(res.transactions);
        setTotalPages(res.total_pages ?? 1);
        setTotalCount(res.total ?? 0);
      })
      .catch((err) => setError(err.message || "Failed to load transactions"))
      .finally(() => setLoading(false));
  }, [accessToken, typeFilter, page, start_date, end_date, refresh]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetchTransactions(); }, [fetchTransactions]);


  async function handleDelete(id: string) {
    if (!accessToken) return;
    setDeletingId(id);
    try {
      await transactionsApi.delete(accessToken, id);
      setTransactions((prev) => prev.filter((t) => t.id !== id));
    } catch {
      // silent fail — could show a toast here
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <SurfaceCard id="recent-transactions" className="p-0 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 border-b border-white/8">
        <h3 className="font-outfit font-semibold text-text-primary text-lg whitespace-nowrap">
          Recent Activity
        </h3>

        {/* Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <SelectPill
            value={typeFilter}
            options={TYPE_OPTIONS}
            onChange={(v) => setTypeFilter(v as TypeFilter)}
          />
        </div>
      </div>

      {/* Body */}
      {error ? (
        <div className="p-6 text-center text-sm text-red-400">{error}</div>
      ) : loading ? (
        <div className="flex flex-col divide-y divide-white/8">
          {[...Array(4)].map((_, i) => (
            <SkeletonRow key={i} />
          ))}
        </div>
      ) : transactions.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex flex-col divide-y divide-white/8">
          {transactions.map((tx) => (
            <div
              key={tx.id}
              className="group flex items-center justify-between p-5 hover:bg-white/[0.03] transition-colors"
            >
              {/* Left: icon + meta */}
              <div className="flex items-center gap-4">
                <div
                  className={`p-2.5 rounded-full flex-shrink-0 ${
                    tx.type === "INCOME"
                      ? "bg-emerald-400/10 text-emerald-400"
                      : "bg-red-400/10 text-red-400"
                  }`}
                >
                  {tx.type === "INCOME" ? (
                    <ArrowUpRight size={18} />
                  ) : (
                    <ArrowDownRight size={18} />
                  )}
                </div>
                <div className="flex flex-col">
                  <span className="font-medium text-text-primary text-sm leading-snug">
                    {tx.description || "—"}
                  </span>
                  <span className="text-xs text-text-secondary mt-0.5">
                    {formatDate(tx.occurred_at)}
                  </span>
                </div>
              </div>

              {/* Right: amount + badge + delete */}
              <div className="flex items-center gap-3">
                <div className="flex flex-col items-end gap-1">
                  <span
                    className={`font-mono font-semibold text-sm ${
                      tx.type === "INCOME"
                        ? "text-emerald-400"
                        : "text-text-primary"
                    }`}
                  >
                    {tx.type === "INCOME" ? "+" : "−"}
                    {formatINR(tx.amount)}
                  </span>
                  <Badge
                    variant={tx.type === "INCOME" ? "success" : "default"}
                    className="text-[10px] px-2 py-0 uppercase tracking-wide"
                  >
                    {tx.category.replace(/_/g, " ")}
                  </Badge>
                </div>

                <button
                  onClick={() => handleDelete(tx.id)}
                  disabled={deletingId === tx.id}
                  aria-label="Delete transaction"
                  className="
                    opacity-0 group-hover:opacity-100
                    p-1.5 rounded-lg text-text-secondary
                    hover:text-red-400 hover:bg-red-400/10
                    transition-all disabled:opacity-40
                  "
                >
                  {deletingId === tx.id ? (
                    <svg
                      className="animate-spin h-3.5 w-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8H4z"
                      />
                    </svg>
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-white/8 text-sm">
          <span className="text-text-secondary">
            {totalCount.toLocaleString("en-IN")} transactions &mdash; page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg border border-white/10 text-text-secondary text-xs
                         hover:border-white/20 hover:text-text-primary transition-colors
                         disabled:opacity-30 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg border border-white/10 text-text-secondary text-xs
                         hover:border-white/20 hover:text-text-primary transition-colors
                         disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </SurfaceCard>
  );
}
