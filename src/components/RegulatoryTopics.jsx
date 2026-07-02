export default function RegulatoryTopics({
  aneelTopics = [],
  mmeTopics = [],
  showAneel = true,
  showMme = true,
  onViewAneel,
  onViewMme,
  onOpenItem,
  t,
}) {
  const badgeColor = (status) => {
    if (status === "Em andamento" || status === "In progress") return "border-blue-200 bg-blue-100 text-blue-700";
    if (status === "Iniciado" || status === "Started") return "border-purple-200 bg-purple-100 text-purple-700";
    if (status === "Concluído" || status === "Completed") return "border-emerald-200 bg-emerald-100 text-emerald-700";
    if (status === "Aberta" || status === "Open") return "border-blue-200 bg-blue-100 text-blue-700";
    if (status === "Encerrada" || status === "Closed") return "border-slate-200 bg-slate-100 text-slate-600";
    return "border-slate-200 bg-slate-100 text-slate-600";
  };

  const Section = ({ number, title, topics, onViewAll, onOpenItem }) => (
    <div className="flex h-[460px] flex-col rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
            {number}
          </div>
          <h2 className="text-base font-semibold text-slate-800">{title}</h2>
        </div>

        <button onClick={onViewAll} className="text-xs font-bold text-[#3f5b70] hover:underline">
          {t.viewAll}
        </button>
      </div>

      <div className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {topics.map((topic) => (
          <button key={topic.title} onClick={() => onOpenItem?.(topic)} className="w-full rounded-2xl border border-slate-100 bg-slate-50/60 p-3 text-left transition hover:bg-white hover:shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-[13px] font-semibold leading-tight text-slate-800">{topic.title}</h3>
              {topic.status && <span className={`shrink-0 rounded-full border px-2 py-1 text-[9px] font-bold ${badgeColor(topic.status)}`}>{topic.status}</span>}
            </div>

            {topic.detail && <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-slate-600">{topic.detail}</p>}

            <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-2">
              <span className="text-[11px] font-semibold text-slate-400">{topic.agency || "RegDesk"}</span>
              {topic.change && <span className="text-[11px] font-semibold text-slate-400">{topic.change}</span>}
            </div>
          </button>
        ))}

        {topics.length === 0 && <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-400">{t.noTopics}</div>}
      </div>
    </div>
  );

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {showAneel && (
        <div id="aneel">
          <Section number="04" title={t.aneelTopics} topics={aneelTopics} onViewAll={onViewAneel} onOpenItem={onOpenItem} />
        </div>
      )}

      {showMme && (
        <div id="mme">
          <Section number="05" title={t.mmeTopics} topics={mmeTopics} onViewAll={onViewMme} onOpenItem={onOpenItem} />
        </div>
      )}
    </div>
  );
}
