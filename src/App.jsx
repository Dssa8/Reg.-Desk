import { useState } from "react";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Highlights from "./components/Highlights";
import RegulatoryTopics from "./components/RegulatoryTopics";
import PublicParticipation from "./components/PublicParticipation";
import Auctions from "./components/Auctions";
import ItemCard from "./components/ItemCard";
import EditionBar from "./components/EditionBar";
import Login from "./components/Login";

import { getClientById } from "./clients";
import editions from "./data/editions";
import { UI_TEXT, localizeEdition, localizeEditionMeta } from "./i18n";
import { getPrimaryChip, ChipList } from "./lib/chips";

// Valor do chip principal (card + filtro de nível na página completa).
const getBadgeValue = getPrimaryChip;

function FullPage({
  title,
  items = [],
  onBack,
  t,
  edition,
  activeEdition,
  hasPreviousEdition,
  hasNextEdition,
  onPreviousEdition,
  onNextEdition,
  onOpenHistory,
  language,
  onChangeLanguage,
}) {
  const [search, setSearch] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);

  const levels = [...new Set(items.map((item) => getBadgeValue(item)).filter(Boolean))];

  const filteredItems = items.filter((item) => {
    const text = `${item.title || ""} ${item.summary || ""} ${item.subtitle || ""} ${item.detail || ""}`.toLowerCase();
    const matchesSearch = text.includes(search.toLowerCase());
    const itemLevel = getBadgeValue(item);
    const matchesLevel = !selectedLevel || itemLevel === selectedLevel;
    return matchesSearch && matchesLevel;
  });

  return (
    <div>
      <button onClick={onBack} className="font-heading mb-5 text-[14px] text-[#3f5b70]">
        {t.backToDashboard}
      </button>

      <div className="rounded-3xl bg-gradient-to-br from-[#3a5570] via-[#2b3f56] to-[#1d2b38] px-8 py-6 text-white shadow-lg">
        <div className="mb-6">
          <EditionBar
            edition={edition}
            activeEdition={activeEdition}
            hasPreviousEdition={hasPreviousEdition}
            hasNextEdition={hasNextEdition}
            onPreviousEdition={onPreviousEdition}
            onNextEdition={onNextEdition}
            language={language}
            onChangeLanguage={onChangeLanguage}
            onOpenHistory={onOpenHistory}
            t={t}
          />
        </div>

        <p className="font-heading text-[12px] uppercase tracking-[0.3em] text-[#9FBE86]">
          REGDESK
        </p>

        <h1 className="font-heading mt-3 text-[32px] leading-tight tracking-tight text-white">
          {title}
        </h1>

        <p className="font-body mt-3 max-w-3xl text-[16px] leading-relaxed text-slate-300">
          {t.fullPageIntro}
        </p>

        <div className="mt-5 grid gap-4 md:grid-cols-[1fr_220px]">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t.searchPlaceholder}
            className="font-body rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-[15px] text-white outline-none placeholder:text-slate-300"
          />

          <div className="relative">
            <select
              value={selectedLevel}
              onChange={(e) => setSelectedLevel(e.target.value)}
              className="font-body w-full appearance-none rounded-2xl border border-white/10 bg-white/10 px-4 py-3 pr-10 text-[15px] text-white outline-none"
            >
              <option value="" className="text-slate-800">{t.all}</option>
              {levels.map((level) => (
                <option key={level} value={level} className="text-slate-800">{level}</option>
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
          <ItemCard
            key={`${item.title}-${index}`}
            item={item}
            onClick={() => setSelectedItem(item)}
            surface="page"
            footerLeft={item.agency || "RegDesk"}
            openLabel={t.open}
            deadlineLabel={t.deadline}
          />
        ))}
      </div>

      {filteredItems.length === 0 && (
        <div className="font-body mt-6 rounded-3xl bg-white p-10 text-center text-[15px] text-slate-500">
          {t.noFilteredItems}
        </div>
      )}

      {selectedItem && (
        <ItemModal item={selectedItem} onClose={() => setSelectedItem(null)} t={t} />
      )}
    </div>
  );
}

function ItemModal({ item, onClose, t }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
      <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-heading text-lg text-slate-800">{item.title}</h2>
            <ChipList item={item} t={t} className="mt-3" />
          </div>

          <button onClick={onClose} className="text-sm font-bold text-slate-400 hover:text-slate-700">✕</button>
        </div>

        <p className="font-body mt-5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
          {item.detail || item.summary || t.textMissing}
        </p>

        {item.notes && (
          <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 px-4 py-2.5">
            <p className="font-heading text-[10px] uppercase tracking-[0.18em] text-slate-400">{t.notes}</p>
            <p className="font-body mt-0.5 whitespace-pre-line text-sm leading-snug text-slate-600">{item.notes}</p>
          </div>
        )}

        {item.link && (
          <a href={item.link} target="_blank" rel="noreferrer" className="font-heading mt-6 inline-block text-sm text-[#3f5b70]">
            {t.openSource}
          </a>
        )}
      </div>
    </div>
  );
}

function CompactSection({ id, number, title, data = [], emptyTitle, emptyDescription, onViewAll, onOpenItem, defaultAgency, t }) {
  return (
    <div id={id} className="flex h-[360px] flex-col rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">{number}</div>
          <h2 className="font-heading text-base text-slate-800">{title}</h2>
        </div>

        <button onClick={onViewAll} className="font-heading text-xs text-[#3f5b70] hover:underline">{t.viewAll}</button>
      </div>

      <div className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {data.length > 0 ? (
          data.map((item, index) => (
            <ItemCard
              key={`${item.title}-${index}`}
              item={item}
              onClick={() => onOpenItem(item)}
              footerLeft={item.agency || defaultAgency || "RegDesk"}
              openLabel={t.open}
            />
          ))
        ) : (
          <div className="flex min-h-[150px] items-center justify-center rounded-2xl bg-slate-50 p-6 text-center">
            <div>
              <p className="text-sm font-semibold text-slate-500">{emptyTitle}</p>
              <p className="mt-1 max-w-xs text-xs leading-relaxed text-slate-400">{emptyDescription}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("dashboard");
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHomeItem, setSelectedHomeItem] = useState(null);
  const [activeEditionIndex, setActiveEditionIndex] = useState(0);
  const [language, setLanguage] = useState("pt");
  const [client, setClient] = useState(() => {
    try {
      return getClientById(localStorage.getItem("regdesk_client"));
    } catch {
      return null;
    }
  });

  const handleLogin = (loggedClient) => {
    setClient(loggedClient);
    try {
      localStorage.setItem("regdesk_client", loggedClient.id);
    } catch {
      /* ignore */
    }
  };

  const handleLogout = () => {
    setClient(null);
    try {
      localStorage.removeItem("regdesk_client");
    } catch {
      /* ignore */
    }
  };

  if (!client) {
    return <Login onLogin={handleLogin} />;
  }

  const t = UI_TEXT[language];
  const rawActiveEdition = editions[activeEditionIndex];
  const edition = localizeEdition(rawActiveEdition.data, language);
  const activeEdition = localizeEditionMeta(rawActiveEdition, language);
  const localizedEditions = editions.map((item) => ({ ...localizeEditionMeta(item, language), data: localizeEdition(item.data, language) }));

  const hasPreviousEdition = activeEditionIndex > 0;
  const hasNextEdition = activeEditionIndex < editions.length - 1;

  const buildHistoryCalendarDays = () => {
    const reference = new Date(`${activeEdition.date}T00:00:00`);
    const firstDay = new Date(reference.getFullYear(), reference.getMonth(), 1);
    const blanks = firstDay.getDay();
    const daysInMonth = new Date(reference.getFullYear(), reference.getMonth() + 1, 0).getDate();
    return [...Array.from({ length: blanks }, () => ""), ...Array.from({ length: daysInMonth }, (_, index) => String(index + 1))];
  };

  const historyDays = buildHistoryCalendarDays();
  const activeEditionDate = new Date(`${activeEdition.date}T00:00:00`);
  const historyMonth = edition.month || "";

  const getEditionForDay = (day) => {
    if (!day) return null;
    return editions.find((item) => {
      const date = new Date(`${item.date}T00:00:00`);
      return date.getFullYear() === activeEditionDate.getFullYear() && date.getMonth() === activeEditionDate.getMonth() && date.getDate() === Number(day);
    });
  };

  const pageConfig = {
    "aneel-agenda": [t.allAneelAgenda, edition.aneelAgenda || []],
    "published-rules": [t.allPublishedRules, edition.publishedRules || []],
    highlights: [t.allHighlights, edition.highlights || []],
    aneel: [t.allAneelTopics, edition.aneelTopics || []],
    mme: [t.allMmeTopics, edition.mmeTopics || []],
    "public-participation": [t.allPublicParticipation, edition.publicParticipation || []],
    auctions: [t.allAuctions, edition.auctions || []],
    agenda: [t.fullAgenda, edition.agenda?.events || []],
  };

  if (page !== "dashboard" && pageConfig[page]) {
    const [title, items] = pageConfig[page];
    return (
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar agenda={edition.agenda} t={t} onNavigate={setPage} activePage={page} clientName={client.name} onLogout={handleLogout} />
        <main className="min-w-0 flex-1 overflow-hidden p-8">
          <FullPage
  title={title}
  items={items}
  onBack={() => setPage("dashboard")}
  t={t}

  edition={edition}
  activeEdition={activeEdition}

  hasPreviousEdition={hasPreviousEdition}
  hasNextEdition={hasNextEdition}

  onOpenHistory={() => setShowHistory(true)}

  onPreviousEdition={() =>
    setActiveEditionIndex(activeEditionIndex - 1)
  }

  onNextEdition={() =>
    setActiveEditionIndex(activeEditionIndex + 1)
  }

  language={language}
  onChangeLanguage={(lang) => {
    setLanguage(lang);
    setSelectedHomeItem(null);
  }}
/>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar agenda={edition.agenda} t={t} onNavigate={setPage} activePage={page} clientName={client.name} onLogout={handleLogout} />

      {showHistory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-heading text-xl text-slate-800">{t.historyTitle}</h2>
                <p className="font-body mt-1 text-sm text-slate-500">{t.historyIntro}</p>
              </div>

              <button onClick={() => setShowHistory(false)} className="text-sm font-bold text-slate-400 hover:text-slate-700">✕</button>
            </div>

            <div className="mt-6 rounded-3xl bg-slate-50 p-5">
              <div className="flex items-center justify-between">
                <h3 className="font-card-title text-slate-800">{historyMonth}</h3>
                <span className="font-body text-xs text-slate-500">{editions.length} {t.availableEditions}</span>
              </div>

              <div className="mt-5 grid grid-cols-7 gap-2 text-center text-xs font-bold text-slate-400">
                {t.weekdays.map((day, index) => <div key={`${day}-${index}`}>{day}</div>)}
              </div>

              <div className="mt-2 grid grid-cols-7 gap-2">
                {historyDays.map((day, index) => {
                  const editionForDay = getEditionForDay(day);
                  const editionIndex = editionForDay ? editions.findIndex((item) => item.id === editionForDay.id) : -1;

                  return (
                    <button
                      key={`${day}-${index}`}
                      disabled={!editionForDay}
                      onClick={() => {
                        if (editionIndex >= 0) {
                          setActiveEditionIndex(editionIndex);
                          setShowHistory(false);
                        }
                      }}
                      className={`h-10 rounded-xl text-sm transition ${editionForDay ? "bg-slate-800 font-bold text-white hover:bg-slate-700" : day ? "bg-white text-slate-400" : "bg-transparent"}`}
                    >
                      {day}
                    </button>
                  );
                })}
              </div>

              <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                <div className="h-2.5 w-2.5 rounded-full bg-slate-800"></div>
                {t.editionPublished}
              </div>
            </div>

            <div className="mt-6">
              <h3 className="font-heading mb-3 text-sm text-slate-700">{t.latestEditions}</h3>
              <div className="space-y-3">
                {localizedEditions.map((item, index) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveEditionIndex(index);
                      setShowHistory(false);
                    }}
                    className={`w-full rounded-2xl border p-4 text-left transition ${index === activeEditionIndex ? "border-[#3f5b70] bg-slate-100" : "border-slate-100 bg-slate-50 hover:bg-white hover:shadow-sm"}`}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-card-title text-slate-800">{item.label}</p>
                        <p className="font-body mt-1 text-sm text-slate-500">{item.data?.period || item.data?.month}</p>
                      </div>
                      <span className="font-heading text-xs text-[#3f5b70]">{t.open}</span>
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
          language={language}
          onChangeLanguage={(lang) => {
            setLanguage(lang);
            setSelectedHomeItem(null);
          }}
          clientLogo={client.logo}
          clientName={client.name}
          t={t}
        />

        <div id="highlights" className="mt-6 scroll-mt-6">
          <Highlights data={edition.highlights || []} onViewAll={() => setPage("highlights")} t={t} />
        </div>

        <div className="mt-6 grid grid-cols-2 gap-6">
          <CompactSection
            id="aneel-agenda"
            number="02"
            title={t.aneelAgenda}
            data={edition.aneelAgenda || []}
            emptyTitle={t.noAgendaItems}
            emptyDescription={t.noAgendaItemsDesc}
            onViewAll={() => setPage("aneel-agenda")}
            onOpenItem={(item) => setSelectedHomeItem(item)}
            defaultAgency="ANEEL"
            t={t}
          />

          <CompactSection
            id="published-rules"
            number="03"
            title={t.publishedRules}
            data={edition.publishedRules || []}
            emptyTitle={t.noPublishedRules}
            emptyDescription={t.noPublishedRulesDesc}
            onViewAll={() => setPage("published-rules")}
            onOpenItem={(item) => setSelectedHomeItem(item)}
            t={t}
          />
        </div>

        <div className="mt-6">
          <RegulatoryTopics
            aneelTopics={edition.aneelTopics || []}
            mmeTopics={edition.mmeTopics || []}
            showAneel={true}
            showMme={true}
            onViewAneel={() => setPage("aneel")}
            onViewMme={() => setPage("mme")}
            onOpenItem={(item) => setSelectedHomeItem(item)}
            t={t}
          />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <PublicParticipation data={edition.publicParticipation || []} onViewAll={() => setPage("public-participation")} onOpenItem={(item) => setSelectedHomeItem(item)} t={t} />
          <Auctions data={edition.auctions || []} onViewAll={() => setPage("auctions")} onOpenItem={(item) => setSelectedHomeItem(item)} t={t} />
        </div>

        {selectedHomeItem && <ItemModal item={selectedHomeItem} onClose={() => setSelectedHomeItem(null)} t={t} />}
      </main>
    </div>
  );
}

export default App;
