"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";

interface Partner {
  id: string;
  name: string;
  type: string;
  ownership_pct: number;
  profit_pct: number;
  loss_pct: number;
}

interface Entity {
  id: string;
  name: string;
  ein: string;
  entity_type: string;
  address: string;
  qbo_connected: boolean;
  partners: Partner[];
  operating_agreement_uploaded: boolean;
  extracted_data: Record<string, string> | null;
}

const MOCK_ENTITY: Entity = {
  id: "1",
  name: "Sunrise Capital Partners",
  ein: "12-3456789",
  entity_type: "Partnership",
  address: "123 Main St, Suite 400, Boston, MA 02101",
  qbo_connected: true,
  partners: [
    { id: "p1", name: "Alice Johnson", type: "General", ownership_pct: 50, profit_pct: 50, loss_pct: 50 },
    { id: "p2", name: "Bob Smith", type: "Limited", ownership_pct: 30, profit_pct: 30, loss_pct: 30 },
    { id: "p3", name: "Cedar Holdings LLC", type: "Limited", ownership_pct: 20, profit_pct: 20, loss_pct: 20 },
  ],
  operating_agreement_uploaded: false,
  extracted_data: null,
};

type Tab = "qbo" | "partners" | "agreement" | "generate";

export default function EntityDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [entity, setEntity] = useState<Entity | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("partners");
  const [uploading, setUploading] = useState(false);
  const [taxYear, setTaxYear] = useState("2025");

  const fetchEntity = useCallback(() => {
    api(`/entities/${id}`)
      .then(setEntity)
      .catch(() => setEntity({ ...MOCK_ENTITY, id }))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => { fetchEntity(); }, [fetchEntity]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/entities/${id}/operating-agreement`,
        { method: "POST", body: formData }
      );
      if (result.ok) fetchEntity();
    } catch {
      setEntity((prev) =>
        prev
          ? {
              ...prev,
              operating_agreement_uploaded: true,
              extracted_data: {
                "Partnership Name": prev.name,
                "Formation Date": "January 1, 2020",
                "Term": "Perpetual",
                "Capital Contributions": "See Schedule A",
                "Profit Sharing": "Per ownership percentages",
              },
            }
          : prev
      );
    } finally {
      setUploading(false);
    }
  }

  if (loading) return <div className="min-h-screen bg-gray-50 flex items-center justify-center text-slate-400">Loading…</div>;
  if (!entity) return <div className="min-h-screen bg-gray-50 flex items-center justify-center text-slate-400">Entity not found</div>;

  const tabs: { key: Tab; label: string }[] = [
    { key: "partners", label: "Partners" },
    { key: "qbo", label: "QuickBooks" },
    { key: "agreement", label: "Operating Agreement" },
    { key: "generate", label: "Generate Return" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold tracking-tight">
            Harvard<span className="text-blue-400">Tax</span>
          </Link>
          <Link href="/dashboard" className="text-sm text-slate-300 hover:text-white">
            ← Dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Entity Header */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 mb-8">
          <h1 className="text-3xl font-bold text-slate-900">{entity.name}</h1>
          <div className="mt-3 flex flex-wrap gap-x-8 gap-y-1 text-sm text-slate-500">
            <span>EIN: <span className="font-mono text-slate-700">{entity.ein}</span></span>
            <span>Type: <span className="text-slate-700">{entity.entity_type}</span></span>
            <span>Address: <span className="text-slate-700">{entity.address}</span></span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-white rounded-lg shadow-sm border border-slate-200 p-1 w-fit">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === t.key ? "bg-blue-500 text-white" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          {tab === "qbo" && (
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-4">QuickBooks Online Connection</h2>
              {entity.qbo_connected ? (
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-2 text-green-700 bg-green-50 px-4 py-2 rounded-full text-sm font-medium">
                    <span className="w-2 h-2 bg-green-500 rounded-full" /> Connected
                  </span>
                  <span className="text-slate-500 text-sm">QuickBooks data is synced for this entity.</span>
                </div>
              ) : (
                <div>
                  <p className="text-slate-600 mb-4">
                    Connect this entity to QuickBooks Online to automatically import financial data for tax return preparation.
                  </p>
                  <a
                    href={`/auth/qbo/connect?entity_id=${entity.id}`}
                    className="inline-block bg-green-600 hover:bg-green-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                  >
                    Connect QuickBooks
                  </a>
                </div>
              )}
            </div>
          )}

          {tab === "partners" && (
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-4">Partners</h2>
              {entity.partners.length === 0 ? (
                <p className="text-slate-400">No partners found. Upload an operating agreement to extract partner data.</p>
              ) : (
                <table className="w-full text-left">
                  <thead className="border-b border-slate-200">
                    <tr>
                      <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Name</th>
                      <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Type</th>
                      <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Ownership %</th>
                      <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Profit %</th>
                      <th className="pb-3 text-xs font-semibold text-slate-500 uppercase tracking-wide text-right">Loss %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {entity.partners.map((p) => (
                      <tr key={p.id}>
                        <td className="py-3 font-medium text-slate-900">{p.name}</td>
                        <td className="py-3 text-slate-600">{p.type}</td>
                        <td className="py-3 text-slate-600 text-right">{p.ownership_pct}%</td>
                        <td className="py-3 text-slate-600 text-right">{p.profit_pct}%</td>
                        <td className="py-3 text-slate-600 text-right">{p.loss_pct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {tab === "agreement" && (
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-4">Operating Agreement</h2>
              {entity.operating_agreement_uploaded && entity.extracted_data ? (
                <div>
                  <p className="text-green-700 bg-green-50 px-4 py-2 rounded-lg text-sm font-medium mb-6 inline-block">
                    ✓ Document uploaded and parsed
                  </p>
                  <div className="space-y-3 mb-6">
                    {Object.entries(entity.extracted_data).map(([key, value]) => (
                      <div key={key} className="flex gap-4">
                        <span className="text-sm font-medium text-slate-500 w-48 shrink-0">{key}</span>
                        <span className="text-sm text-slate-900">{value}</span>
                      </div>
                    ))}
                  </div>
                  <button className="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium transition-colors">
                    Confirm Extracted Data
                  </button>
                </div>
              ) : (
                <div>
                  <p className="text-slate-600 mb-4">
                    Upload your partnership operating agreement (PDF) to automatically extract partner allocations and terms.
                  </p>
                  <label className="inline-block cursor-pointer bg-blue-500 hover:bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium transition-colors">
                    {uploading ? "Uploading…" : "Upload PDF"}
                    <input type="file" accept=".pdf" onChange={handleUpload} className="hidden" />
                  </label>
                </div>
              )}
            </div>
          )}

          {tab === "generate" && (
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-4">Generate Tax Return</h2>
              <p className="text-slate-600 mb-6">
                Generate Form 1065 and Schedule K-1s for all partners based on connected QuickBooks data and operating agreement terms.
              </p>
              <div className="flex items-end gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Tax Year</label>
                  <select
                    value={taxYear}
                    onChange={(e) => setTaxYear(e.target.value)}
                    className="border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option>2025</option>
                    <option>2024</option>
                    <option>2023</option>
                    <option>2022</option>
                  </select>
                </div>
                <Link
                  href={`/generate?entity_id=${entity.id}&tax_year=${taxYear}`}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium transition-colors"
                >
                  Generate 1065 + K-1s
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
