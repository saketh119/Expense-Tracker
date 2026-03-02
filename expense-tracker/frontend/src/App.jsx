import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:5000";

// ─── API helpers ────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}, token = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

// ─── Status config ───────────────────────────────────────────────────────────
const STATUS = {
  draft:     { label: "Draft",     color: "#94a3b8", bg: "#f1f5f9", dot: "#64748b" },
  submitted: { label: "Submitted", color: "#3b82f6", bg: "#eff6ff", dot: "#2563eb" },
  approved:  { label: "Approved",  color: "#22c55e", bg: "#f0fdf4", dot: "#16a34a" },
  rejected:  { label: "Rejected",  color: "#ef4444", bg: "#fef2f2", dot: "#dc2626" },
};

const CATEGORIES = ["travel", "meals", "software", "equipment", "training", "other"];

// ─── Components ──────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const s = STATUS[status] || STATUS.draft;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "3px 10px", borderRadius: 20,
      background: s.bg, color: s.dot,
      fontSize: 12, fontWeight: 600, letterSpacing: "0.03em",
      border: `1px solid ${s.color}30`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.dot }} />
      {s.label}
    </span>
  );
}

function Button({ children, onClick, variant = "primary", disabled, small }) {
  const styles = {
    primary:   { background: "#0f172a", color: "#fff", border: "none" },
    secondary: { background: "#fff",    color: "#0f172a", border: "1px solid #e2e8f0" },
    danger:    { background: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca" },
    success:   { background: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0" },
    ghost:     { background: "transparent", color: "#64748b", border: "none" },
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        ...styles[variant],
        padding: small ? "5px 12px" : "8px 18px",
        borderRadius: 8, cursor: disabled ? "not-allowed" : "pointer",
        fontWeight: 600, fontSize: small ? 12 : 14,
        opacity: disabled ? 0.5 : 1,
        transition: "opacity 0.15s, transform 0.1s",
        fontFamily: "inherit",
      }}
    >
      {children}
    </button>
  );
}

function Input({ label, value, onChange, type = "text", required, options }) {
  const style = {
    width: "100%", padding: "8px 12px", borderRadius: 8,
    border: "1px solid #e2e8f0", fontSize: 14, fontFamily: "inherit",
    background: "#fff", outline: "none", boxSizing: "border-box",
  };
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#475569", marginBottom: 5 }}>
        {label}{required && <span style={{ color: "#ef4444" }}> *</span>}
      </label>
      {options ? (
        <select value={value} onChange={e => onChange(e.target.value)} style={style}>
          <option value="">Select…</option>
          {options.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
        </select>
      ) : (
        <input type={type} value={value} onChange={e => onChange(e.target.value)} style={style} />
      )}
    </div>
  );
}

function Modal({ title, onClose, children }) {
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
    }} onClick={onClose}>
      <div style={{
        background: "#fff", borderRadius: 16, padding: 28, width: 480, maxWidth: "calc(100vw - 32px)",
        boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>{title}</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", color: "#94a3b8" }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Login Page ──────────────────────────────────────────────────────────────
function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("alice@demo.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const DEMO_USERS = [
    { email: "alice@demo.com", role: "Employee" },
    { email: "bob@demo.com",   role: "Employee" },
    { email: "carol@demo.com", role: "Manager"  },
  ];

  async function handleLogin() {
    setLoading(true); setError("");
    try {
      const data = await apiFetch("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      onLogin(data.token, data.user);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh", background: "#0f172a",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'DM Sans', system-ui, sans-serif",
    }}>
      <div style={{ width: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>💳</div>
          <h1 style={{ color: "#fff", margin: "0 0 8px", fontSize: 28, fontWeight: 800 }}>ExpenseFlow</h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: 15 }}>Expense approval, simplified</p>
        </div>

        <div style={{ background: "#fff", borderRadius: 16, padding: 28, boxShadow: "0 20px 60px rgba(0,0,0,0.3)" }}>
          <Input label="Email" value={email} onChange={setEmail} type="email" required />
          <Input label="Password" value={password} onChange={setPassword} type="password" required />

          {error && (
            <div style={{ background: "#fef2f2", color: "#dc2626", padding: "10px 14px", borderRadius: 8, fontSize: 13, marginBottom: 14 }}>
              {error}
            </div>
          )}

          <Button onClick={handleLogin} disabled={loading}>
            {loading ? "Signing in…" : "Sign In →"}
          </Button>

          <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid #f1f5f9" }}>
            <p style={{ fontSize: 11, color: "#94a3b8", margin: "0 0 12px", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600 }}>
              Demo accounts (password: password123)
            </p>
            {DEMO_USERS.map(u => (
              <button key={u.email} onClick={() => { setEmail(u.email); setPassword("password123"); }}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  width: "100%", background: email === u.email ? "#f8fafc" : "transparent",
                  border: "1px solid " + (email === u.email ? "#e2e8f0" : "transparent"),
                  borderRadius: 8, padding: "8px 12px", cursor: "pointer", marginBottom: 4, fontFamily: "inherit",
                }}>
                <span style={{ fontSize: 13, color: "#1e293b", fontWeight: 500 }}>{u.email}</span>
                <span style={{ fontSize: 11, color: "#64748b", fontWeight: 600,
                  padding: "2px 8px", background: "#f1f5f9", borderRadius: 10 }}>{u.role}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Expense Form ─────────────────────────────────────────────────────────────
function ExpenseForm({ token, expense, onSave, onClose }) {
  const [form, setForm] = useState({
    title: expense?.title || "",
    amount: expense?.amount || "",
    category: expense?.category || "",
    description: expense?.description || "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const set = (k) => (v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit() {
    setSaving(true); setError("");
    try {
      const method = expense ? "PATCH" : "POST";
      const path = expense ? `/expenses/${expense.id}` : "/expenses/";
      const saved = await apiFetch(path, { method, body: JSON.stringify(form) }, token);
      onSave(saved);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={expense ? "Edit Expense" : "New Expense"} onClose={onClose}>
      <Input label="Title" value={form.title} onChange={set("title")} required />
      <Input label="Amount ($)" value={form.amount} onChange={set("amount")} type="number" required />
      <Input label="Category" value={form.category} onChange={set("category")} options={CATEGORIES} required />
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#475569", marginBottom: 5 }}>Description</label>
        <textarea value={form.description} onChange={e => set("description")(e.target.value)}
          style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0",
            fontSize: 14, fontFamily: "inherit", minHeight: 80, resize: "vertical", boxSizing: "border-box" }} />
      </div>
      {error && <div style={{ background: "#fef2f2", color: "#dc2626", padding: "10px 14px", borderRadius: 8, fontSize: 13, marginBottom: 14 }}>{error}</div>}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} disabled={saving}>{saving ? "Saving…" : expense ? "Save Changes" : "Create Expense"}</Button>
      </div>
    </Modal>
  );
}

// ─── History Modal ───────────────────────────────────────────────────────────
function HistoryModal({ token, expense, onClose }) {
  const [history, setHistory] = useState(null);

  useEffect(() => {
    apiFetch(`/expenses/${expense.id}/history`, {}, token).then(setHistory);
  }, [expense.id, token]);

  return (
    <Modal title={`History — ${expense.title}`} onClose={onClose}>
      {!history ? <div style={{ color: "#94a3b8", textAlign: "center", padding: 20 }}>Loading…</div> : (
        <div>
          {history.map((h, i) => (
            <div key={h.id} style={{ display: "flex", gap: 12, marginBottom: 12 }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: STATUS[h.to_status]?.dot || "#64748b", marginTop: 4 }} />
                {i < history.length - 1 && <div style={{ width: 2, flex: 1, background: "#e2e8f0", marginTop: 4 }} />}
              </div>
              <div style={{ flex: 1, paddingBottom: 12 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 3 }}>
                  {h.from_status && <StatusBadge status={h.from_status} />}
                  {h.from_status && <span style={{ color: "#94a3b8", fontSize: 12 }}>→</span>}
                  <StatusBadge status={h.to_status} />
                </div>
                <div style={{ fontSize: 12, color: "#64748b" }}>
                  by <strong>{h.changed_by}</strong> · {new Date(h.timestamp).toLocaleString()}
                </div>
                {h.note && <div style={{ fontSize: 12, color: "#475569", marginTop: 3, fontStyle: "italic" }}>"{h.note}"</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </Modal>
  );
}

// ─── Action Modal (approve/reject) ───────────────────────────────────────────
function ActionModal({ token, expense, action, onDone, onClose }) {
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    setLoading(true); setError("");
    try {
      const updated = await apiFetch(`/expenses/${expense.id}/${action}`, {
        method: "POST", body: JSON.stringify({ note }),
      }, token);
      onDone(updated);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal title={action === "approve" ? "Approve Expense" : "Reject Expense"} onClose={onClose}>
      <p style={{ color: "#475569", fontSize: 14, margin: "0 0 16px" }}>
        <strong>{expense.title}</strong> — ${expense.amount.toFixed(2)}
      </p>
      <div style={{ marginBottom: 14 }}>
        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#475569", marginBottom: 5 }}>Note (optional)</label>
        <textarea value={note} onChange={e => setNote(e.target.value)}
          placeholder={action === "approve" ? "e.g. Approved for Q1 budget" : "e.g. Please attach receipt"}
          style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid #e2e8f0",
            fontSize: 14, fontFamily: "inherit", minHeight: 80, resize: "vertical", boxSizing: "border-box" }} />
      </div>
      {error && <div style={{ background: "#fef2f2", color: "#dc2626", padding: "10px 14px", borderRadius: 8, fontSize: 13, marginBottom: 14 }}>{error}</div>}
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button variant={action === "approve" ? "success" : "danger"} onClick={handleSubmit} disabled={loading}>
          {loading ? "…" : action === "approve" ? "✓ Approve" : "✗ Reject"}
        </Button>
      </div>
    </Modal>
  );
}

// ─── Expense Card ─────────────────────────────────────────────────────────────
function ExpenseCard({ expense, user, token, onUpdate }) {
  const [modal, setModal] = useState(null); // null | 'edit' | 'history' | 'approve' | 'reject'
  const [loading, setLoading] = useState(null);

  async function doAction(action) {
    if (action === "approve" || action === "reject") { setModal(action); return; }
    setLoading(action);
    try {
      const updated = await apiFetch(`/expenses/${expense.id}/${action}`, { method: "POST" }, token);
      onUpdate(updated);
    } finally {
      setLoading(null);
    }
  }

  const isOwner = expense.user_id === user.id;
  const isManager = user.role === "manager";

  return (
    <>
      <div style={{
        background: "#fff", borderRadius: 12, padding: "18px 20px",
        border: "1px solid #e2e8f0", marginBottom: 10,
        transition: "box-shadow 0.15s",
      }}
        onMouseEnter={e => e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.08)"}
        onMouseLeave={e => e.currentTarget.style.boxShadow = "none"}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
              <span style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>{expense.title}</span>
              <StatusBadge status={expense.status} />
            </div>
            <div style={{ display: "flex", gap: 12, fontSize: 12, color: "#64748b", flexWrap: "wrap" }}>
              <span>💰 <strong style={{ color: "#0f172a" }}>${expense.amount.toFixed(2)}</strong></span>
              <span>🏷️ {expense.category}</span>
              {isManager && <span>👤 {expense.owner_name}</span>}
              <span>📅 {new Date(expense.created_at).toLocaleDateString()}</span>
            </div>
            {expense.description && (
              <p style={{ margin: "8px 0 0", fontSize: 13, color: "#64748b", fontStyle: "italic" }}>
                {expense.description}
              </p>
            )}
          </div>

          <div style={{ display: "flex", gap: 6, alignItems: "center", marginLeft: 12, flexShrink: 0 }}>
            <Button variant="ghost" small onClick={() => setModal("history")}>📋 History</Button>

            {isOwner && expense.status === "draft" && (
              <>
                <Button variant="secondary" small onClick={() => setModal("edit")}>✏️ Edit</Button>
                <Button small onClick={() => doAction("submit")} disabled={loading === "submit"}>
                  {loading === "submit" ? "…" : "Submit"}
                </Button>
              </>
            )}

            {isOwner && expense.status === "rejected" && (
              <Button variant="secondary" small onClick={() => doAction("reopen")} disabled={loading === "reopen"}>
                ↩️ Reopen
              </Button>
            )}

            {isManager && expense.status === "submitted" && (
              <>
                <Button variant="danger" small onClick={() => doAction("reject")}>✗ Reject</Button>
                <Button variant="success" small onClick={() => doAction("approve")}>✓ Approve</Button>
              </>
            )}
          </div>
        </div>
      </div>

      {modal === "edit" && (
        <ExpenseForm token={token} expense={expense} onClose={() => setModal(null)}
          onSave={updated => { onUpdate(updated); setModal(null); }} />
      )}
      {modal === "history" && (
        <HistoryModal token={token} expense={expense} onClose={() => setModal(null)} />
      )}
      {(modal === "approve" || modal === "reject") && (
        <ActionModal token={token} expense={expense} action={modal}
          onClose={() => setModal(null)}
          onDone={updated => { onUpdate(updated); setModal(null); }} />
      )}
    </>
  );
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
function Dashboard({ token, user, onLogout }) {
  const [expenses, setExpenses] = useState([]);
  const [filter, setFilter] = useState("all");
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/expenses/", {}, token);
      setExpenses(data);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  function updateExpense(updated) {
    setExpenses(es => es.map(e => e.id === updated.id ? updated : e));
  }

  function addExpense(expense) {
    setExpenses(es => [expense, ...es]);
    setShowForm(false);
  }

  const filtered = filter === "all" ? expenses : expenses.filter(e => e.status === filter);

  const stats = {
    total:     expenses.length,
    draft:     expenses.filter(e => e.status === "draft").length,
    submitted: expenses.filter(e => e.status === "submitted").length,
    approved:  expenses.filter(e => e.status === "approved").length,
    rejected:  expenses.filter(e => e.status === "rejected").length,
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "'DM Sans', system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ background: "#0f172a", padding: "0 24px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center", height: 60 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 22 }}>💳</span>
            <span style={{ color: "#fff", fontWeight: 800, fontSize: 18 }}>ExpenseFlow</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ color: "#fff", fontSize: 14, fontWeight: 600 }}>{user.name}</div>
              <div style={{ color: "#94a3b8", fontSize: 12, textTransform: "capitalize" }}>{user.role}</div>
            </div>
            <Button variant="secondary" small onClick={onLogout}>Sign out</Button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "28px 24px" }}>
        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
          {[
            { label: "Submitted", value: stats.submitted, status: "submitted" },
            { label: "Approved",  value: stats.approved,  status: "approved"  },
            { label: "Rejected",  value: stats.rejected,  status: "rejected"  },
            { label: "Drafts",    value: stats.draft,      status: "draft"     },
          ].map(s => (
            <div key={s.status}
              onClick={() => setFilter(filter === s.status ? "all" : s.status)}
              style={{
                background: filter === s.status ? STATUS[s.status].bg : "#fff",
                border: `1px solid ${filter === s.status ? STATUS[s.status].color + "60" : "#e2e8f0"}`,
                borderRadius: 12, padding: "14px 16px", cursor: "pointer",
                transition: "all 0.15s",
              }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: STATUS[s.status].dot }}>{s.value}</div>
              <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Toolbar */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#0f172a" }}>
              {filter === "all" ? "All Expenses" : `${STATUS[filter]?.label} Expenses`}
            </h2>
            <p style={{ margin: "2px 0 0", fontSize: 13, color: "#64748b" }}>
              {filtered.length} {filtered.length === 1 ? "expense" : "expenses"}
              {filter !== "all" && <button onClick={() => setFilter("all")} style={{ marginLeft: 8, color: "#3b82f6", background: "none", border: "none", cursor: "pointer", fontSize: 13 }}>Clear filter</button>}
            </p>
          </div>
          {user.role === "employee" && (
            <Button onClick={() => setShowForm(true)}>+ New Expense</Button>
          )}
        </div>

        {/* List */}
        {loading ? (
          <div style={{ textAlign: "center", color: "#94a3b8", padding: 40 }}>Loading expenses…</div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: "center", color: "#94a3b8", padding: 60, background: "#fff", borderRadius: 12, border: "1px dashed #e2e8f0" }}>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📭</div>
            <div style={{ fontWeight: 600 }}>No expenses here</div>
            {user.role === "employee" && filter === "all" && (
              <div style={{ marginTop: 12 }}>
                <Button onClick={() => setShowForm(true)}>Create your first expense</Button>
              </div>
            )}
          </div>
        ) : (
          filtered.map(expense => (
            <ExpenseCard key={expense.id} expense={expense} user={user} token={token} onUpdate={updateExpense} />
          ))
        )}
      </div>

      {showForm && (
        <ExpenseForm token={token} expense={null} onClose={() => setShowForm(false)} onSave={addExpense} />
      )}
    </div>
  );
}

// ─── Root ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [auth, setAuth] = useState(() => {
    try {
      const t = sessionStorage.getItem("token");
      const u = sessionStorage.getItem("user");
      return t && u ? { token: t, user: JSON.parse(u) } : null;
    } catch { return null; }
  });

  function handleLogin(token, user) {
    sessionStorage.setItem("token", token);
    sessionStorage.setItem("user", JSON.stringify(user));
    setAuth({ token, user });
  }

  function handleLogout() {
    sessionStorage.clear();
    setAuth(null);
  }

  if (!auth) return <LoginPage onLogin={handleLogin} />;
  return <Dashboard token={auth.token} user={auth.user} onLogout={handleLogout} />;
}
