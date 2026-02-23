import { useState, useEffect } from 'react'
import api, { type DataStats, type UpdateStatus } from '../services/api'

export default function DataSyncPanel() {
  console.log('%c✅ DATA SYNC PANEL RENDERIZADO! Painel está visível!',
    'background: #0066ff; color: #fff; font-size: 16px; padding: 8px; font-weight: bold;')

  const [stats, setStats] = useState<DataStats | null>(null)
  const [status, setStatus] = useState<UpdateStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getDataStats()
      setStats(data)
    } catch (err) {
      setError(`Erro ao buscar estatísticas: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  const fetchStatus = async () => {
    try {
      const data = await api.getUpdateStatus()
      setStatus(data)
    } catch (err) {
      console.error('Erro ao buscar status:', err)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchStatus()

    // Poll status every 5 seconds when downloading
    const interval = setInterval(() => {
      if (downloading) {
        fetchStatus()
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [downloading])

  const handleDownload = async (fullHistorical: boolean) => {
    try {
      setDownloading(true)
      setError(null)
      setSuccess(null)

      const result = await api.runUpdate(false, fullHistorical)

      setSuccess(
        `✅ Download concluído!\n` +
        `• ${result.total_years} anos baixados\n` +
        `• ${result.stocks} ações atualizadas\n` +
        `• ${result.prices.toLocaleString('pt-BR')} preços inseridos`
      )

      // Refresh stats after download
      await fetchStats()
    } catch (err: any) {
      setError(`❌ Erro no download: ${err.message || err}`)
    } finally {
      setDownloading(false)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    const date = new Date(dateStr)
    return date.toLocaleDateString('pt-BR')
  }

  const getCoveragePercentage = () => {
    if (!stats || !stats.years || stats.years.length === 0) return 0
    const currentYear = new Date().getFullYear()
    const totalYears = currentYear - stats.expected_start_year + 1
    const availableYears = stats.years.length
    return Math.round((availableYears / totalYears) * 100)
  }

  return (
    <div className="w-80 bg-dark-card border-l border-dark-border flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-dark-border">
        <h2 className="text-sm font-semibold text-dark-text flex items-center gap-2">
          <span className="text-lg">📊</span>
          Sincronização de Dados
        </h2>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Stats Card */}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : stats ? (
          <div className="space-y-3">
            {/* Coverage */}
            <div className="bg-dark-bg rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-dark-muted">Cobertura Histórica</span>
                <span className="text-xs font-semibold text-dark-text">
                  {getCoveragePercentage()}%
                </span>
              </div>
              <div className="w-full bg-dark-border rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getCoveragePercentage()}%` }}
                />
              </div>
              <div className="mt-2 text-xs text-dark-muted">
                {stats.years.length} de {new Date().getFullYear() - stats.expected_start_year + 1} anos disponíveis
              </div>
            </div>

            {/* Info Grid */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-dark-bg rounded-lg p-3">
                <div className="text-xs text-dark-muted mb-1">Primeiro Registro</div>
                <div className="text-sm font-semibold text-dark-text">
                  {formatDate(stats.first_date)}
                </div>
              </div>
              <div className="bg-dark-bg rounded-lg p-3">
                <div className="text-xs text-dark-muted mb-1">Último Registro</div>
                <div className="text-sm font-semibold text-dark-text">
                  {formatDate(stats.last_date)}
                </div>
              </div>
              <div className="bg-dark-bg rounded-lg p-3">
                <div className="text-xs text-dark-muted mb-1">Total de Registros</div>
                <div className="text-sm font-semibold text-dark-text">
                  {stats.total_records.toLocaleString('pt-BR')}
                </div>
              </div>
              <div className="bg-dark-bg rounded-lg p-3">
                <div className="text-xs text-dark-muted mb-1">Ações</div>
                <div className="text-sm font-semibold text-dark-text">
                  {stats.total_stocks}
                </div>
              </div>
            </div>

            {/* Status Indicator */}
            <div className={`rounded-lg p-3 ${stats.coverage_complete ? 'bg-green-500/10 border border-green-500/20' : 'bg-yellow-500/10 border border-yellow-500/20'}`}>
              <div className="flex items-center gap-2">
                <span className="text-lg">{stats.coverage_complete ? '✅' : '⚠️'}</span>
                <div className="flex-1">
                  <div className="text-xs font-semibold text-dark-text">
                    {stats.coverage_complete ? 'Completo' : 'Incompleto'}
                  </div>
                  <div className="text-xs text-dark-muted">
                    {stats.coverage_complete
                      ? 'Dados desde 2000 (26 anos)'
                      : 'Dados históricos faltando'
                    }
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* Download Status */}
        {status?.is_running && (
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              <div>
                <div className="text-xs font-semibold text-dark-text">Download em andamento...</div>
                <div className="text-xs text-dark-muted">Aguarde a conclusão</div>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
            <div className="text-xs text-dark-text whitespace-pre-line">{success}</div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            <div className="text-xs text-red-400">{error}</div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-2">
          <button
            onClick={fetchStats}
            disabled={loading || downloading}
            className="w-full px-4 py-2.5 bg-dark-bg hover:bg-dark-border text-dark-text text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span>🔄</span>
            Atualizar Estatísticas
          </button>

          <button
            onClick={() => handleDownload(false)}
            disabled={loading || downloading || status?.is_running}
            className="w-full px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {downloading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Baixando...
              </>
            ) : (
              <>
                <span>📥</span>
                Download Incremental
              </>
            )}
          </button>

          <button
            onClick={() => handleDownload(true)}
            disabled={loading || downloading || status?.is_running}
            className="w-full px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {downloading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Baixando...
              </>
            ) : (
              <>
                <span>🚀</span>
                Download Completo (2000-2026)
              </>
            )}
          </button>
        </div>

        {/* Info Box */}
        <div className="bg-dark-bg rounded-lg p-3 text-xs text-dark-muted space-y-2">
          <p className="font-semibold text-dark-text">ℹ️ Sobre os Downloads:</p>
          <ul className="space-y-1 list-disc list-inside">
            <li><strong>Incremental:</strong> Baixa apenas anos faltantes</li>
            <li><strong>Completo:</strong> Baixa tudo desde 2000 (26 anos)</li>
            <li>Dados em R$ (Real brasileiro)</li>
            <li>Batches de 3 anos para otimização</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
