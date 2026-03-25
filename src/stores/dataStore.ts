import { create } from "zustand"
import type { ColumnMapping } from "@/types/delivery"

type UploadStatus = "idle" | "parsing" | "mapping" | "geocoding" | "indexing" | "done" | "error"

interface DataState {
  uploadStatus: UploadStatus
  uploadProgress: number // 0-100
  totalRows: number
  processedRows: number
  columnMapping: ColumnMapping | null
  errorMessage: string | null
  setUploadStatus: (status: UploadStatus) => void
  setUploadProgress: (progress: number) => void
  setTotalRows: (total: number) => void
  setProcessedRows: (processed: number) => void
  setColumnMapping: (mapping: ColumnMapping | null) => void
  setError: (message: string | null) => void
  reset: () => void
}

const initialState = {
  uploadStatus: "idle" as UploadStatus,
  uploadProgress: 0,
  totalRows: 0,
  processedRows: 0,
  columnMapping: null,
  errorMessage: null,
}

export const useDataStore = create<DataState>((set) => ({
  ...initialState,
  setUploadStatus: (status) => set({ uploadStatus: status }),
  setUploadProgress: (progress) => set({ uploadProgress: progress }),
  setTotalRows: (total) => set({ totalRows: total }),
  setProcessedRows: (processed) => set({ processedRows: processed }),
  setColumnMapping: (mapping) => set({ columnMapping: mapping }),
  setError: (message) => set({ errorMessage: message, uploadStatus: "error" }),
  reset: () => set(initialState),
}))
