import ItemCard from "./ItemCard";

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
  const Section = ({ number, title, topics, onViewAll, onOpenItem }) => (
    <div className="flex h-[460px] flex-col rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
            {number}
          </div>
          <h2 className="font-heading text-base text-slate-800">{title}</h2>
        </div>

        <button onClick={onViewAll} className="font-heading text-xs text-[#3f5b70] hover:underline">
          {t.viewAll}
        </button>
      </div>

      <div className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {topics.map((topic) => (
          <ItemCard
            key={topic.title}
            item={topic}
            onClick={() => onOpenItem?.(topic)}
            footerLeft={topic.agency || "RegDesk"}
            openLabel={t.open}
          />
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
