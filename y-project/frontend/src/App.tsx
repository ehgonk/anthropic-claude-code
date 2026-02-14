import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { RankingPage } from "./pages/RankingPage";
import { ExplorerPage } from "./pages/ExplorerPage";
import { AdminPage } from "./pages/AdminPage";
import { api } from "./services/api";
import { RefreshCw, CheckCircle2, AlertTriangle } from "lucide-react";

type SyncStatus = "syncing" | "success" | "error" | "idle";

function SyncBanner() {
  const [status, setStatus] = useState<SyncStatus>("syncing");
  const [message, setMessage] = useState("Atualizando dados D-1...");

  useEffect(() => {
    let dismissed = false;

    api.syncD1()
      .then((result) => {
        if (dismissed) return;
        setStatus("success");
        setMessage(
          `Dados atualizados: CVM=${result.cvm_records}, B3=${result.b3_records}, Scores=${result.scores_calculated}`
        );
        setTimeout(() => {
          if (!dismissed) setStatus("idle");
        }, 5000);
      })
      .catch((err) => {
        if (dismissed) return;
        setStatus("error");
        setMessage(
          `Erro ao atualizar: ${err instanceof Error ? err.message : "erro desconhecido"}`
        );
        setTimeout(() => {
          if (!dismissed) setStatus("idle");
        }, 8000);
      });

    return () => {
      dismissed = true;
    };
  }, []);

  if (status === "idle") return null;

  return (
    <div
      className={`flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium transition-all ${
        status === "syncing"
          ? "bg-brand-600/20 text-brand-400"
          : status === "success"
            ? "bg-emerald-600/20 text-emerald-400"
            : "bg-red-600/20 text-red-400"
      }`}
    >
      {status === "syncing" && (
        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
      )}
      {status === "success" && <CheckCircle2 className="h-3.5 w-3.5" />}
      {status === "error" && <AlertTriangle className="h-3.5 w-3.5" />}
      <span>{message}</span>
    </div>
  );
}

export default function App() {
  return (
    <>
      <SyncBanner />
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="ranking" element={<RankingPage />} />
          <Route path="explorer" element={<ExplorerPage />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
      </Routes>
    </>
  );
}
