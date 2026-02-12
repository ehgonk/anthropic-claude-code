/**
 * Página de administração — ingestão de dados e recálculo de scores.
 */

import { Database, Download, RefreshCw, AlertTriangle, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { api } from "../services/api";

interface LogEntry {
  time: string;
  message: string;
  type: "info" | "success" | "error";
}

export function AdminPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const addLog = (message: string, type: LogEntry["type"] = "info") => {
    setLogs((prev) => [
      { time: new Date().toLocaleTimeString("pt-BR"), message, type },
      ...prev,
    ]);
  };

  const handleIngest = async (source: "cvm" | "b3", year: number) => {
    setLoading(true);
    addLog(`Iniciando ingestão ${source.toUpperCase()} ${year}...`);
    try {
      const result = await api.triggerIngest(source, year);
      addLog(
        `${source.toUpperCase()} ${year}: ${result.records_inserted} registros inseridos`,
        "success"
      );
    } catch (err) {
      addLog(
        `Erro ${source.toUpperCase()} ${year}: ${err instanceof Error ? err.message : "erro desconhecido"}`,
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    setLoading(true);
    addLog("Recalculando scores...");
    try {
      const result = await api.recalculateScores();
      addLog(`${result.scores_calculated} scores recalculados`, "success");
    } catch (err) {
      addLog(
        `Erro ao recalcular: ${err instanceof Error ? err.message : "erro desconhecido"}`,
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">
          <Database className="mr-2 inline h-6 w-6" />
          Administração
        </h1>
        <p className="text-sm text-gray-500">
          Ingestão de dados e recálculo de scores
        </p>
      </div>

      {/* Ingestão CVM */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Download className="mr-2 inline h-4 w-4" />
            Ingestão CVM (Insider Trading)
          </h2>
        </div>
        <p className="mb-4 text-sm text-gray-400">
          Baixa e importa dados de negociações de administradores do portal dados.cvm.gov.br
        </p>
        <div className="flex flex-wrap gap-2">
          {years.map((year) => (
            <button
              key={`cvm-${year}`}
              onClick={() => handleIngest("cvm", year)}
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              CVM {year}
            </button>
          ))}
        </div>
      </div>

      {/* Ingestão B3 */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <Download className="mr-2 inline h-4 w-4" />
            Ingestão B3 (Cotações COTAHIST)
          </h2>
        </div>
        <p className="mb-4 text-sm text-gray-400">
          Baixa e importa cotações históricas do arquivo COTAHIST da B3
        </p>
        <div className="flex flex-wrap gap-2">
          {years.map((year) => (
            <button
              key={`b3-${year}`}
              onClick={() => handleIngest("b3", year)}
              disabled={loading}
              className="btn-primary disabled:opacity-50"
            >
              B3 {year}
            </button>
          ))}
        </div>
      </div>

      {/* Recálculo */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">
            <RefreshCw className="mr-2 inline h-4 w-4" />
            Recalcular Scores
          </h2>
        </div>
        <p className="mb-4 text-sm text-gray-400">
          Recalcula o score de -100 a +100 para todas as empresas com base nos dados
          mais recentes de insiders, short interest, fluxo e momentum.
        </p>
        <button
          onClick={handleRecalculate}
          disabled={loading}
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Recalcular Todos os Scores
        </button>
      </div>

      {/* Logs */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Log de Operações</h2>
          {logs.length > 0 && (
            <button
              onClick={() => setLogs([])}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              Limpar
            </button>
          )}
        </div>
        <div className="max-h-64 overflow-y-auto space-y-1">
          {logs.length === 0 ? (
            <p className="py-4 text-center text-sm text-gray-600">
              Nenhuma operação executada
            </p>
          ) : (
            logs.map((log, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 rounded px-2 py-1 text-xs font-mono ${
                  log.type === "error"
                    ? "bg-red-500/5 text-red-400"
                    : log.type === "success"
                      ? "bg-emerald-500/5 text-emerald-400"
                      : "text-gray-400"
                }`}
              >
                {log.type === "error" ? (
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
                ) : log.type === "success" ? (
                  <CheckCircle2 className="mt-0.5 h-3 w-3 shrink-0" />
                ) : (
                  <span className="mt-0.5 h-3 w-3 shrink-0 text-center">·</span>
                )}
                <span className="shrink-0 text-gray-600">[{log.time}]</span>
                <span>{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
