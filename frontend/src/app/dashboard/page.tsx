"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Entity {
  id: string;
  name: string;
  ein: string;
  entity_type: string;
  qbo_connected: boolean;
  partner_count: number;
}

const MOCK_ENTITIES: Entity[] = [
  { id: "1", name: "Sunrise Capital Partners", ein: "12-3456789", entity_type: "Partnership", qbo_connected: true, partner_count: 3 },
  { id: "2", name: "Greenfield Ventures LP", ein: "98-7654321", entity_type: "LP", qbo_connected: false, partner_count: 5 },
  { id: "3", name: "Metro Real Estate Holdings", ein: "55-1234567", entity_type: "LLC", qbo_connected: true, partner_count: 2 },
];

export default function DashboardPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", ein: "", entity_type: "Partnership" });

  useEffect(() => {
    api("/entities")
      .then(setEntities)
      .catch(() => setEntities(MOCK_ENTITIES))
      .finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api("/entities", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setEntities((prev) => [...prev, created]);
    } catch {
      const newId = String(Date.now());
      setEntities((prev) => [
        ...prev,
        { ...form, id: newId, qbo_connected: false, partner_count: 0 },
      ]);
    }
    setForm({ name: "", ein: "", entity_type: "Partnership" });
    setShowForm(false);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <header className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold tracking-tight">
            Harvard<span className="text-blue-400">Tax</span>
          </Link>
          <span className="text-sm text-slate-300">Dashboard</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Your Entities</h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium transition-colors"
          >
            + Add Entity
          </button>
        </div>

        {/* Add Entity Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <form
              onSubmit={handleCreate}
              className="bg-white rounded-xl shadow-xl p-8 w-full max-w-md space-y-5"
            >
              <h2 className="text-xl font-bold text-slate-900">New Entity</h2>
              <input
                required
                placeholder="Entity name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                required
                placeholder="EIN (e.g. 12-3456789)"
                value={form.ein}
                onChange={(e) => setForm({ ...form, ein: e.target.value })}
                className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={form.entity_type}
                onChange={(e) => setForm({ ...form, entity_type: e.target.value })}
                className="w-full border border-slate-300 rounded-lg px-4 py-2.5 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option>Partnership</option>
                <option>LP</option>
                <option>LLC</option>
                <option>LLP</option>
              </select>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-500 hover:bg-blue-600 text-white px-5 py-2 rounded-lg font-medium"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Entity List */}
        {loading ? (
          <div className="text-center py-20 text-slate-400">Loading…</div>
        ) : entities.length === 0 ? (
          <div className="text-center py-20 text-slate-400">
            No entities yet. Click &quot;Add Entity&quot; to get started.
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Name</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">EIN</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Type</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">QBO</th>
                  <th className="px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">Partners</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {entities.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <Link href={`/entities/${e.id}`} className="text-blue-600 hover:underline font-medium">
                        {e.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-mono text-sm">{e.ein}</td>
                    <td className="px-6 py-4 text-slate-600">{e.entity_type}</td>
                    <td className="px-6 py-4">
                      {e.qbo_connected ? (
                        <span className="inline-flex items-center gap-1 text-green-700 bg-green-50 px-2.5 py-0.5 rounded-full text-xs font-medium">
                          <span className="w-1.5 h-1.5 bg-green-500 rounded-full" /> Connected
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">Not connected</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-600">{e.partner_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
