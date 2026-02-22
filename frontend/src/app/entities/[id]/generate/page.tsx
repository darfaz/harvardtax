"use client";

import Link from "next/link";
import { useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

const LINE_DESCRIPTIONS: Record<string, string> = {
  "1a": "Gross receipts or sales",
  "1b": "Returns and allowances",
  "2": "Cost of goods sold",
  "3": "Gross profit",
  "7": "Other income",
  "8": "Total income",
  "9": "Salaries and wages",
  "10": "Guaranteed payments",
  "11": "Repairs and maintenance",
  "12": "Bad debts",
  "13": "Rent",
  "14": "Taxes and licenses",
  "15": "Interest",
  "16a": "Depreciation",
  "20": "Other deductions",
  "21": "Total deductions",
  "22": "Ordinary business income (loss)",
};

interface LineDetail {
  account_name: string;
  amount: number;
}

interface MappedLine {
  line: string;
  amount: number;
  line_details: LineDetail[];
}

interface UnmappedAccount {
  account_name: string;
  qbo_subtype: string;
  amount: number;
}

interface K1Info {
  partner_name: string;
  path: string;
}

interface GenerateResult {
  mapped_data: MappedLine[];
  unmapped_accounts: UnmappedAccount[];
  form_1065_path?: string;
  k1s?: K1Info[];
}

type Status = "idle" | "loading" | "success" | "error";

export default function GeneratePage() {
  const params = useParams();
  const entityId = params.id as string;
  const [taxYear, setTaxYear] = useState("2024");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [expandedLines, setExpandedLines] = useState<Set<string>>(new Set());
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [savingOverrides, setSavingOverrides] = useState(false);

  async function handleGenerate() {
    setStatus("loading");
    setError("");
    setResult(null);
    try {
      const data = await api(
        `/tax-returns/${entityId}/generate?tax_year=${taxYear}`,
        { method: "POST" }
      );
      setResult(data);
      setStatus("success");
      setOverrides({});
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
      setStatus("error");
    }
  }

  async function handleSaveOverrides() {
    const entries = Object.entries(overrides).filter(([, v]) => v);
    if (entries.length === 0) return;
    setSavingOverrides(true);
    try {
      await api(`/tax-returns/${entityId}/${taxYear}/override`, {
        method: "POST",
        body: JSON.stringify({ overrides: entries.map(([account_name, line]) => ({ account_name, line })) }),
      });
      // Re-generate to reflect overrides
      await handleGenerate();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save overrides");
    } finally {
      setSavingOverrides(false);
    }
  }

  function toggleLine(line: string) {
    setExpandedLines((prev) => {
      const next = new Set(prev);
      if (next.has(line)) next.delete(line);
      else next.add(line);
      return next;
    });
  }

  const fmt = (n: number) =>
    n.toLocaleString("en-US", { style: "currency", currency: "USD" });

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold tracking-tight">
            Harvard<span className="text-blue-400">Tax</span>
          </Link>
          <Link
            href={`/entities/${entityId}`}
            className="text-sm text-slate-300 hover:text-white"
          >
            ← Back to Entity
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        {/* Generate Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            Generate Tax Return
          </h1>
          <p className="text-slate-600 mb-6">
            Generate Form 1065 and Schedule K-1s from QuickBooks data.
          </p>
          <div className="flex items-end gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Tax Year
              </label>
              <select
                value={taxYear}
                onChange={(e) => setTaxYear(e.target.value)}
                className="border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="2025">2025</option>
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
              </select>
            </div>
            <button
              onClick={handleGenerate}
              disabled={status === "loading"}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-6 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              {status === "loading" && (
                <svg
                  className="animate-spin h-4 w-4"
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
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
              )}
              {status === "loading" ? "Generating…" : "Generate 1065 + K-1s"}
            </button>
          </div>

          {status === "error" && (
            <div className="mt-4 bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          {status === "success" && (
            <div className="mt-4 bg-green-50 text-green-700 px-4 py-3 rounded-lg text-sm font-medium">
              ✓ Tax return generated successfully
            </div>
          )}
        </div>

        {/* Mapping Review Table */}
        {result && result.mapped_data && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4">
              Form 1065 Mapping Review
            </h2>
            <table className="w-full text-left">
              <thead className="border-b border-slate-200">
                <tr>
                  <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-20">
                    Line
                  </th>
                  <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Description
                  </th>
                  <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Object.keys(LINE_DESCRIPTIONS).map((line) => {
                  const mapped = result.mapped_data.find(
                    (m) => m.line === line
                  );
                  const amount = mapped?.amount ?? 0;
                  const details = mapped?.line_details ?? [];
                  const hasMapped = details.length > 0;
                  const isExpanded = expandedLines.has(line);

                  return (
                    <tr key={line} className="group">
                      <td className="py-3 align-top">
                        <button
                          onClick={() => hasMapped && toggleLine(line)}
                          className={`font-mono text-sm font-medium px-2 py-0.5 rounded ${
                            hasMapped
                              ? "bg-green-100 text-green-800 cursor-pointer hover:bg-green-200"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {line}
                        </button>
                      </td>
                      <td className="py-3 align-top">
                        <div className="text-slate-900 text-sm">
                          {LINE_DESCRIPTIONS[line]}
                        </div>
                        {isExpanded && details.length > 0 && (
                          <div className="mt-2 ml-2 space-y-1">
                            {details.map((d, i) => (
                              <div
                                key={i}
                                className="text-xs text-slate-500 flex justify-between max-w-md"
                              >
                                <span>{d.account_name}</span>
                                <span className="font-mono">
                                  {fmt(d.amount)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="py-3 text-right align-top font-mono text-sm text-slate-900">
                        {fmt(amount)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Unmapped Accounts */}
        {result &&
          result.unmapped_accounts &&
          result.unmapped_accounts.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
              <h2 className="text-xl font-bold text-slate-900 mb-1">
                Unmapped Accounts
              </h2>
              <p className="text-sm text-slate-500 mb-4">
                These QBO accounts could not be automatically mapped to a 1065
                line. Assign them manually below.
              </p>
              <table className="w-full text-left mb-6">
                <thead className="border-b border-slate-200">
                  <tr>
                    <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      Account
                    </th>
                    <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      QBO Subtype
                    </th>
                    <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">
                      Amount
                    </th>
                    <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      Assign to Line
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {result.unmapped_accounts.map((acct, i) => (
                    <tr key={i}>
                      <td className="py-3 text-sm text-slate-900 font-medium">
                        {acct.account_name}
                      </td>
                      <td className="py-3 text-sm text-slate-600">
                        {acct.qbo_subtype}
                      </td>
                      <td className="py-3 text-sm text-slate-900 text-right font-mono">
                        {fmt(acct.amount)}
                      </td>
                      <td className="py-3">
                        <select
                          value={overrides[acct.account_name] || ""}
                          onChange={(e) =>
                            setOverrides((prev) => ({
                              ...prev,
                              [acct.account_name]: e.target.value,
                            }))
                          }
                          className="border border-slate-300 rounded-md px-3 py-1.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">— Select —</option>
                          {Object.entries(LINE_DESCRIPTIONS).map(
                            ([line, desc]) => (
                              <option key={line} value={line}>
                                {line}: {desc}
                              </option>
                            )
                          )}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button
                onClick={handleSaveOverrides}
                disabled={
                  savingOverrides ||
                  Object.values(overrides).filter(Boolean).length === 0
                }
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-slate-300 text-white px-5 py-2.5 rounded-lg font-medium transition-colors"
              >
                {savingOverrides ? "Saving…" : "Save Overrides & Regenerate"}
              </button>
            </div>
          )}

        {/* Download Section */}
        {result && (result.form_1065_path || (result.k1s && result.k1s.length > 0)) && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4">
              Download Forms
            </h2>
            <div className="flex flex-wrap gap-3">
              {result.form_1065_path && (
                <a
                  href={`${apiBase}${result.form_1065_path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-lg font-medium transition-colors"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3"
                    />
                  </svg>
                  Form 1065 PDF
                </a>
              )}
              {result.k1s?.map((k1, i) => (
                <a
                  key={i}
                  href={`${apiBase}${k1.path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-900 px-5 py-2.5 rounded-lg font-medium transition-colors"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v3a2 2 0 002 2h14a2 2 0 002-2v-3"
                    />
                  </svg>
                  K-1: {k1.partner_name}
                </a>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
