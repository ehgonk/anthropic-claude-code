/**
 * Barra de busca de empresas com autocomplete.
 */

import { Search } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type Company } from "../services/api";

interface SearchBarProps {
  onSelect: (ticker: string) => void;
}

export function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Company[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const search = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const companies = await api.getCompanies(q);
      setResults(companies.slice(0, 8));
      setShowDropdown(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(query), 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, search]);

  // Fecha dropdown ao clicar fora
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSelect = (ticker: string) => {
    setQuery(ticker);
    setShowDropdown(false);
    onSelect(ticker);
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          placeholder="Buscar por ticker ou empresa..."
          className="input w-full pl-10"
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-600 border-t-brand-500" />
          </div>
        )}
      </div>

      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-gray-700 bg-gray-800 py-1 shadow-xl">
          {results.map((c) => (
            <button
              key={c.ticker}
              onClick={() => handleSelect(c.ticker)}
              className="flex w-full items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-gray-700"
            >
              <span className="font-mono text-sm font-bold text-brand-400">
                {c.ticker}
              </span>
              <span className="truncate text-sm text-gray-300">{c.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
