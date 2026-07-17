import EditionBar from "./EditionBar";
import intelidesk from "../assets/intelidesk.png";

function Header({
  edition,
  activeEdition,
  hasPreviousEdition,
  hasNextEdition,
  onPreviousEdition,
  onNextEdition,
  onOpenHistory,
  language,
  onChangeLanguage,
  clientLogo,
  clientName,
  t,
}) {
  const metrics = [
    { id: "highlights", value: edition.highlights?.length ?? 0, label: t.highlightsMetric },
    { id: "aneel-agenda", value: edition.aneelAgenda?.length ?? 0, label: t.agendaMetric },
    { id: "published-rules", value: edition.publishedRules?.length ?? 0, label: t.rulesMetric },
    { id: "aneel", value: edition.aneelTopics?.length ?? 0, label: t.pendingAneelMetric },
    { id: "mme", value: edition.mmeTopics?.length ?? 0, label: t.pendingMmeMetric },
    { id: "public-participation", value: edition.publicParticipation?.length ?? 0, label: t.participationMetric },
    { id: "auctions", value: edition.auctions?.length ?? 0, label: t.auctionsMetric },
  ];

  const goToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <header className="rounded-3xl bg-gradient-to-br from-[#344A61] via-[#021A34] to-[#021A34] px-8 pt-4 pb-2 text-white shadow-lg">
      <div className="mb-3">
        <EditionBar
          edition={edition}
          activeEdition={activeEdition}
          hasPreviousEdition={hasPreviousEdition}
          hasNextEdition={hasNextEdition}
          onPreviousEdition={onPreviousEdition}
          onNextEdition={onNextEdition}
          onOpenHistory={onOpenHistory}
          language={language}
          onChangeLanguage={onChangeLanguage}
          t={t}
        />
      </div>

      <div className="grid grid-cols-[1fr_220px] gap-8">
        <div className="mt-2">
          <img
            src={intelidesk}
            alt={t.dashboardTitle}
            className="h-9 w-auto object-contain"
          />

          <p className="font-body mt-3 max-w-3xl text-[14px] leading-relaxed text-slate-300">
            {t.dashboardSubtitle}
          </p>
        </div>

        <div className="flex flex-col items-end text-right">
          <p className="font-heading text-[10px] uppercase tracking-[0.28em] text-slate-400">
            {t.preparedFor}
          </p>

          <img
            src={clientLogo}
            alt={clientName}
            className="mt-1 h-11 object-contain"
          />

          <div className="mt-2">
            <p className="font-heading text-[10px] uppercase tracking-[0.25em] text-slate-400">
              {t.lastUpdated}
            </p>

            <p className="font-body mt-0.5 text-[14px] text-slate-200">
              {edition.updatedAt || t.noUpdate}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-1 grid grid-cols-3 gap-x-4 gap-y-3 border-t border-white/10 pt-2 sm:grid-cols-4 lg:grid-cols-7">
        {metrics.map((metric) => (
          <button
            key={metric.id}
            type="button"
            onClick={() => goToSection(metric.id)}
            className="group flex flex-col items-center rounded-xl px-2 py-1 text-center transition hover:bg-white/5"
          >
            <p className="font-heading text-[24px] leading-none text-white transition group-hover:text-[#86A876]">
              {metric.value}
            </p>
            <p className="font-body mt-1.5 text-[10px] uppercase leading-none tracking-[0.12em] text-slate-400 transition group-hover:text-slate-200">
              {metric.label}
            </p>
          </button>
        ))}
      </div>
    </header>
  );
}

export default Header;