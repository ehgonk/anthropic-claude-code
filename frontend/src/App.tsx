import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { RankingPage } from "./pages/RankingPage";
import { ExplorerPage } from "./pages/ExplorerPage";
import { AdminPage } from "./pages/AdminPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="ranking" element={<RankingPage />} />
        <Route path="explorer" element={<ExplorerPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}
