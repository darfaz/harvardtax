import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="text-xl font-bold tracking-tight">
            Harvard<span className="text-blue-400">Tax</span>
          </span>
          <Link
            href="/dashboard"
            className="text-sm bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Sign In
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-slate-900 text-white pt-16 pb-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl font-extrabold tracking-tight leading-tight">
            Partnership Tax Returns,{" "}
            <span className="text-blue-400">Automated</span>
          </h1>
          <p className="mt-6 text-lg text-slate-300 max-w-2xl mx-auto">
            Connect QuickBooks&nbsp;→ Upload your Operating Agreement&nbsp;→ Get
            Form&nbsp;1065 + K‑1s in minutes, not weeks.
          </p>
          <Link
            href="/dashboard"
            className="mt-10 inline-block bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg px-8 py-3.5 rounded-xl transition-colors"
          >
            Get Started →
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-white flex-1">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-center text-3xl font-bold text-slate-900 mb-14">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: "📊",
                title: "QBO Integration",
                desc: "One-click QuickBooks Online sync pulls your partnership's chart of accounts and trial balance automatically.",
              },
              {
                icon: "📄",
                title: "AI Agreement Parsing",
                desc: "Upload your operating agreement and our AI extracts partner allocations, special provisions, and capital accounts.",
              },
              {
                icon: "⚡",
                title: "Instant PDF Generation",
                desc: "Generate IRS-ready Form 1065 and Schedule K-1s as downloadable PDFs — review, sign, and file.",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="bg-slate-50 rounded-2xl p-8 border border-slate-200 hover:shadow-lg transition-shadow"
              >
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  {f.title}
                </h3>
                <p className="text-slate-600 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 text-sm py-8 px-6 text-center">
        © {new Date().getFullYear()} HarvardTax. All rights reserved.
      </footer>
    </div>
  );
}
