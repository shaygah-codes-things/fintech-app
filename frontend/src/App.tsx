import { ToastProvider, useToast } from "./ui/Toast";
import { AuthProvider, useAuth } from "./auth";
import { PayoutsRefreshProvider } from "./context/PayoutsRefresh";
import { PayoutForm } from "./components/PayoutForm";
import { PayoutList } from "./components/PayoutList";

function Header() {
  const { me, loading, login, doLogout, refresh } = useAuth();
  const { notify } = useToast();

  return (
    <header
      style={{
        padding: "12px 16px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 24,
      }}
    >
      <div className="h1" style={{ fontSize: 28, margin: 0 }}>
        Fintech App
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        {loading ? (
          <span>Loading…</span>
        ) : me ? (
          <>
            <span style={{ fontSize: 14, color: "var(--muted)" }}>
              {me.email}
            </span>
            <button
              className="btn"
              onClick={() => {
                doLogout().then(() => notify("✅ Logged out", "success"));
              }}
            >
              Logout
            </button>
            <button className="btn" onClick={() => refresh()}>
              Refresh
            </button>
          </>
        ) : (
          <button className="btn" onClick={login}>
            Login with GitHub
          </button>
        )}
      </div>
    </header>
  );
}

function Home() {
  const { me } = useAuth();
  return (
    <main className="container">
      {me ? (
        <PayoutsRefreshProvider>
          <PayoutForm />
          <PayoutList />
        </PayoutsRefreshProvider>
      ) : (
        <section className="card" style={{ padding: 20 }}>
          <p style={{ marginBottom: 8 }}>You’re not logged in.</p>
          <p>Click “Login with GitHub” above to start.</p>
        </section>
      )}
    </main>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Header />
        <Home />
      </AuthProvider>
    </ToastProvider>
  );
}
