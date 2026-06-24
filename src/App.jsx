import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Highlights from "./components/Highlights";
import RegulatoryTopics from "./components/RegulatoryTopics";
import PublicParticipation from "./components/PublicParticipation";
import Auctions from "./components/Auctions";

import editions from "./data/editions";

function FullPage({ title, items = [], onBack }) {
  const [search, setSearch] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("Todos");
  const [selectedItem, setSelectedItem] = useState(null);

  const badgeClass = (value) => {
    if (value === "Crítica" || value === "Crítico")
      return "bg-red-100 text-red-700 border-red-200";

    if (value === "Alta" || value === "Alto")
      return "bg-orange-100 text-orange-700 border-orange-200";

    if (value === "Média" || value === "Médio")
      return "bg-amber-100 text-amber-700 border-amber-200";

    return "bg-emerald-100 text-emerald-700 border-emerald-200";
  };

  const levels = [
    "Todos",
    ...new Set(items.map((item) => item.level || item.impact).filter(Boolean)),
  ];

  const filteredItems = items.filter((item) => {
    const text = `${item.title || ""} ${item.summary || ""} ${
      item.subtitle || ""
    } ${item.detail || ""}`.toLowerCase();

    const matchesSearch = text.includes(search.toLowerCase());
    const itemLevel = item.level || item.impact;
    const matchesLevel =
      selectedLevel === "Todos" || itemLevel === selectedLevel;

    return matchesSearch && matchesLevel;
  });

  return (
    <div>
      <button
        onClick={onBack}
        className="mb-5 text-xs font-bold text-[#3f5b70]"
      >
        ← Voltar ao painel
      </button>

      <div className="rounded-3xl bg-[#2b3f56] p-6 text-white shadow-lg">
        <p className="text-[10px] uppercase tracking-[0.3em] text-slate-300">
          REGDESK
        </p>

        <h1 className="mt-3 text-[28px] font-semibold tracking-tight">
          {title}
        </h1>

        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-200">
          Consulte todos os itens da edição, filtre por criticidade e abra cada
          item para ver a análise completa.
        </p>

        <div className="mt-5 grid md:grid-cols-[1fr_220px] gap-4">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por tema, órgão ou palavra-chave..."
            className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white placeholder:text-slate-300 outline-none"
          />

          <div className="relative">
  <select
    value={selectedLevel}
    onChange={(e) => setSelectedLevel(e.target.value)}
    className="w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 pr-10 text-sm text-white outline-none appearance-none"
  >
    {levels.map((level) => (
      <option key={level} value={level} className="text-slate-800">
        {level}
      </option>
    ))}
  </select>

  <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-slate-300">
    ▾
  </span>
</div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {filteredItems.map((item, index) => (
          <button
            key={`${item.title}-${index}`}
            onClick={() => setSelectedItem(item)}
            className="flex min-h-[140px] flex-col rounded-3xl border border-slate-100 bg-white p-3 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-md"
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-[13px] font-semibold leading-snug text-slate-800">
                {item.title}
              </h2>

              {(item.level || item.impact) && (
                <span
                  className={`shrink-0 rounded-full border px-2 py-1 text-[9px] font-bold ${badgeClass(
                    item.level || item.impact
                  )}`}
                >
                  {item.level || item.impact}
                </span>
              )}
            </div>

            {(item.detail || item.summary || item.subtitle) && (
  <p className="mt-2 line-clamp-3 text-[12px] leading-relaxed text-slate-600">
    {item.detail || item.summary || item.subtitle}
  </p>
)}

            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2">
              <span className="text-[11px] font-semibold text-slate-400">
                {item.agency || "RegDesk"}
              </span>

              <span className="text-xs font-bold text-[#3f5b70]">
                Abrir →
              </span>
            </div>
          </button>
        ))}
      </div>

      {filteredItems.length === 0 && (
        <div className="mt-6 rounded-3xl bg-white p-10 text-center text-sm text-slate-500">
          Nenhum item encontrado com os filtros selecionados.
        </div>
      )}

      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">
                  {selectedItem.title}
                </h2>

                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  {selectedItem.status && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 font-semibold text-slate-600">
                      Status: {selectedItem.status}
                    </span>
                  )}

                  {(selectedItem.level || selectedItem.impact) && (
                    <span
                      className={`rounded-full border px-2 py-1 font-semibold ${badgeClass(
                        selectedItem.level || selectedItem.impact
                      )}`}
                    >
                      Criticidade: {selectedItem.level || selectedItem.impact}
                    </span>
                  )}

                  {selectedItem.deadline && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 font-semibold text-slate-600">
                      Prazo: {selectedItem.deadline}
                    </span>
                  )}

                  {selectedItem.date && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 font-semibold text-slate-600">
                      Data: {selectedItem.date}
                    </span>
                  )}

                  {selectedItem.agency && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 font-semibold text-slate-600">
                      Órgão: {selectedItem.agency}
                    </span>
                  )}
                </div>
              </div>

              <button
                onClick={() => setSelectedItem(null)}
                className="text-sm font-bold text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            {selectedItem.detail ? (
              <p className="mt-5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
                {selectedItem.detail}
              </p>
            ) : (
              <p className="mt-5 text-sm leading-relaxed text-slate-600">
                Texto completo não informado.
              </p>
            )}

            {selectedItem.link && (
              <a
                href={selectedItem.link}
                target="_blank"
                rel="noreferrer"
                className="mt-6 inline-block text-sm font-bold text-[#3f5b70]"
              >
                Abrir fonte →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  const [page, setPage] = useState("dashboard");
const [showHistory, setShowHistory] = useState(false);
const [selectedHomeItem, setSelectedHomeItem] = useState(null);
const [activeEditionIndex, setActiveEditionIndex] = useState(0);

  const edition = editions[activeEditionIndex].data;
  const activeEdition = editions[activeEditionIndex];

  const hasPreviousEdition = activeEditionIndex > 0;
  const hasNextEdition = activeEditionIndex < editions.length - 1;

if (page === "aneel-agenda") {
  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar agenda={edition.agenda} />
      <main className="flex-1 p-8">
        <FullPage
          title="Todas as Pautas ANEEL"
          items={edition.aneelAgenda || []}
          onBack={() => setPage("dashboard")}
        />
      </main>
    </div>
  );
}

if (page === "published-rules") {
  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar agenda={edition.agenda} />
      <main className="flex-1 p-8">
        <FullPage
          title="Todos os Normativos Publicados"
          items={edition.publishedRules || []}
          onBack={() => setPage("dashboard")}
        />
      </main>
    </div>
  );
}

  if (page === "highlights") {
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} />

        <main className="flex-1 p-8">
          <FullPage
            title="Todos os Destaques"
            items={edition.highlights}
            onBack={() => setPage("dashboard")}
          />
        </main>
      </div>
    );
  }

  if (page === "aneel") {
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} />

        <main className="flex-1 p-8">
          <FullPage
            title="Todos os Temas ANEEL"
            items={edition.aneelTopics}
            onBack={() => setPage("dashboard")}
          />
        </main>
      </div>
    );
  }

  if (page === "mme") {
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} />

        <main className="flex-1 p-8">
          <FullPage
            title="Todos os Temas MME"
            items={edition.mmeTopics}
            onBack={() => setPage("dashboard")}
          />
        </main>
      </div>
    );
  }

  if (page === "consultations") {
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} />

        <main className="flex-1 p-8">
          <FullPage
            title="Todas as Consultas Públicas"
            items={edition.consultations}
            onBack={() => setPage("dashboard")}
          />
        </main>
      </div>
    );
  }

  if (page === "auctions") {
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} />

        <main className="flex-1 p-8">
          <FullPage
            title="Todos os Leilões"
            items={edition.auctions}
            onBack={() => setPage("dashboard")}
          />
        </main>
      </div>
    );
  }

  if (page === "agenda") {
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} />

        <main className="flex-1 p-8">
          <FullPage
            title="Agenda Completa"
            items={edition.agenda?.events || []}
            onBack={() => setPage("dashboard")}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar agenda={edition.agenda} />

      {showHistory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-slate-800">
                  Histórico de Edições
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Selecione uma edição semanal para consultar o conteúdo
                  histórico.
                </p>
              </div>

              <button
                onClick={() => setShowHistory(false)}
                className="text-sm font-bold text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            <div className="mt-6 rounded-3xl bg-slate-50 p-5">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-800">Junho 2026</h3>

                <span className="text-xs font-semibold text-slate-500">
                  {editions.length} edição disponível
                </span>
              </div>

              <div className="mt-5 grid grid-cols-7 gap-2 text-center text-xs font-bold text-slate-400">
                <div>S</div>
                <div>T</div>
                <div>Q</div>
                <div>Q</div>
                <div>S</div>
                <div>S</div>
                <div>D</div>
              </div>

              <div className="mt-2 grid grid-cols-7 gap-2">
                {[
                  "",
                  "",
                  "",
                  "",
                  "",
                  "",
                  "1",
                  "2",
                  "3",
                  "4",
                  "5",
                  "6",
                  "7",
                  "8",
                  "9",
                  "10",
                  "11",
                  "12",
                  "13",
                  "14",
                  "15",
                  "16",
                  "17",
                  "18",
                  "19",
                  "20",
                  "21",
                  "22",
                  "23",
                  "24",
                  "25",
                  "26",
                  "27",
                  "28",
                  "29",
                  "30",
                ].map((day, index) => {
                  const hasEdition = day === "12";

                  return (
                    <button
                      key={`${day}-${index}`}
                      disabled={!hasEdition}
                      onClick={() => {
                        setActiveEditionIndex(0);
                        setShowHistory(false);
                      }}
                      className={`
                        h-10 rounded-xl text-sm transition
                        ${
                          hasEdition
                            ? "bg-slate-800 text-white font-bold hover:bg-slate-700"
                            : day
                            ? "bg-white text-slate-400"
                            : "bg-transparent"
                        }
                      `}
                    >
                      {day}
                    </button>
                  );
                })}
              </div>

              <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                <div className="h-2.5 w-2.5 rounded-full bg-slate-800"></div>
                Edição publicada
              </div>
            </div>

            <div className="mt-6">
              <h3 className="mb-3 text-sm font-bold text-slate-700">
                Últimas edições
              </h3>

              <div className="space-y-3">
                {editions.map((item, index) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveEditionIndex(index);
                      setShowHistory(false);
                    }}
                    className={`
                      w-full rounded-2xl border p-4 text-left transition
                      ${
                        index === activeEditionIndex
                          ? "border-[#3f5b70] bg-slate-100"
                          : "border-slate-100 bg-slate-50 hover:bg-white hover:shadow-sm"
                      }
                    `}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-bold text-slate-800">
                          {item.label}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">
                          {item.data?.period || item.data?.month}
                        </p>
                      </div>

                      <span className="text-xs font-bold text-[#3f5b70]">
                        Abrir →
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <main className="flex-1 p-8">
        <Header
  edition={edition}
  activeEdition={activeEdition}
  hasPreviousEdition={hasPreviousEdition}
  hasNextEdition={hasNextEdition}
  onPreviousEdition={() => setActiveEditionIndex(activeEditionIndex - 1)}
  onNextEdition={() => setActiveEditionIndex(activeEditionIndex + 1)}
  onOpenHistory={() => setShowHistory(true)}
/>

<div id="highlights" className="mt-5">
  <Highlights
    data={edition.highlights.slice(0, 3)}
    onViewAll={() => setPage("highlights")}
  />
</div>

<div className="mt-6 grid grid-cols-2 gap-6">
  <div
    id="aneel-agenda"
    className="rounded-3xl bg-white p-5 shadow-sm border border-slate-100"
  >
    <div className="mb-4 flex items-center justify-between">
     <div className="flex items-center gap-3">
    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
      02
    </div>

    <h2 className="text-base font-semibold text-slate-800">
      Pautas ANEEL
    </h2>
  </div>

  <button
  onClick={() => setPage("aneel-agenda")}
  className="text-xs font-bold text-[#3f5b70] hover:underline"
>
  Ver tudo →
</button>
</div>

    <div className="space-y-3">
      {(edition.aneelAgenda || []).length > 0 ? (
        edition.aneelAgenda.slice(0, 3).map((item, index) => (
         <button
  key={`${item.title}-${index}`}
  onClick={() => setSelectedHomeItem(item)}
  className="w-full rounded-2xl border border-slate-100 bg-slate-50/60 p-3 text-left transition hover:bg-white hover:shadow-sm"
>
            <h3 className="text-[13px] font-semibold leading-tight text-slate-800">
              {item.title}
            </h3>

            {(item.detail || item.summary) && (
              <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-slate-600">
                {item.detail || item.summary}
              </p>
            )}

            <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
              <span className="text-[11px] font-semibold text-slate-400">
                {item.agency || "ANEEL"}
              </span>

              <span className="text-xs font-bold text-[#3f5b70]">
  Abrir →
</span>
            </div>
          </button>
        ))
      ) : (
        <div className="flex min-h-[150px] items-center justify-center rounded-2xl bg-slate-50 p-6 text-center">
          <div>
            <p className="text-sm font-semibold text-slate-500">
              Nenhuma pauta cadastrada.
            </p>

            <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-400">
              Os itens aparecerão automaticamente quando forem incluídos no Excel.
            </p>
          </div>
        </div>
      )}
    </div>
  </div>

  <div
    id="published-rules"
    className="rounded-3xl bg-white p-5 shadow-sm border border-slate-100"
  >
    <div className="mb-4 flex items-center justify-between">
  <div className="flex items-center gap-3">
    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
      03
    </div>

    <h2 className="text-base font-semibold text-slate-800">
      Normativos Publicados
    </h2>
  </div>

  <button
  onClick={() => setPage("published-rules")}
  className="text-xs font-bold text-[#3f5b70] hover:underline"
>
  Ver tudo →
</button>
</div>

    <div className="space-y-3">
      {(edition.publishedRules || []).length > 0 ? (
        edition.publishedRules.slice(0, 3).map((item, index) => (
  <button
    key={`${item.title}-${index}`}
    onClick={() => setSelectedHomeItem(item)}
    className="w-full rounded-2xl border border-slate-100 bg-slate-50/60 p-3 text-left transition hover:bg-white hover:shadow-sm"
  >
            <h3 className="text-[13px] font-semibold leading-tight text-slate-800">
              {item.title}
            </h3>

            {(item.detail || item.summary) && (
              <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-slate-600">
                {item.detail || item.summary}
              </p>
            )}

            <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
              <span className="text-[11px] font-semibold text-slate-400">
                {item.agency || "RegDesk"}
              </span>

              <span className="text-xs font-bold text-[#3f5b70]">
  Abrir →
</span>
            </div>
          </button>
        ))
      ) : (
        <div className="flex min-h-[150px] items-center justify-center rounded-2xl bg-slate-50 p-6 text-center">
          <div>
            <p className="text-sm font-semibold text-slate-500">
              Nenhum normativo cadastrado.
            </p>

            <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-400">
              Os normativos aparecerão automaticamente quando forem incluídos no Excel.
            </p>
          </div>
        </div>
      )}
    </div>
  </div>
</div>

<div className="mt-6">
  <RegulatoryTopics
    aneelTopics={edition.aneelTopics.slice(0, 5)}
    mmeTopics={edition.mmeTopics.slice(0, 5)}
    showAneel={true}
    showMme={true}
    onViewAneel={() => setPage("aneel")}
    onViewMme={() => setPage("mme")}
    onOpenItem={(item) => setSelectedHomeItem(item)}
  />
</div>

<div id="auctions" className="mt-6">
  <Auctions
    data={edition.auctions.slice(0, 3)}
    onViewAll={() => setPage("auctions")}
onOpenItem={(item) => setSelectedHomeItem(item)}
  />
</div>
{selectedHomeItem && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
    <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">
            {selectedHomeItem.title}
            {selectedHomeItem.agency && (
  <div className="mt-3">
    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
      Órgão: {selectedHomeItem.agency}
    </span>
  </div>
)}
          </h2>
        </div>

        <button
          onClick={() => setSelectedHomeItem(null)}
          className="text-sm font-bold text-slate-400 hover:text-slate-700"
        >
          ✕
        </button>
      </div>

      <p className="mt-5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
        {selectedHomeItem.detail ||
          selectedHomeItem.summary ||
          "Texto completo não informado."}
      </p>
    </div>
  </div>
)}
      </main>
    </div>
  );
}

export default App;