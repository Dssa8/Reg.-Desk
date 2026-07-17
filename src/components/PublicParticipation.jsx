import ItemCard from "./ItemCard";

export default function PublicParticipation({ data = [], onViewAll, onOpenItem, t }) {
  return (
    <div id="public-participation" className="flex h-[360px] flex-col rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#021A34] text-xs font-bold text-white">06</div>
          <h2 className="font-heading text-base font-semibold leading-tight text-slate-800">{t.publicParticipation}</h2>
        </div>

        <button type="button" onClick={onViewAll} className="font-heading shrink-0 text-xs text-[#344A61] hover:underline">
          {t.viewAll}
        </button>
      </div>

      <div className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {data.length > 0 ? (
          data.map((item, index) => (
            <ItemCard
              key={`${item.title}-${index}`}
              item={item}
              onClick={() => onOpenItem?.(item)}
              footerLeft={item.agency || "InteliDesk"}
              openLabel={t.open}
              deadlineLabel={t.deadline}
            />
          ))
        ) : (
          <div className="flex h-full items-center justify-center rounded-2xl bg-slate-50">
            <div className="px-8 text-center">
              <p className="text-sm font-semibold text-slate-500">{t.noPublicParticipation}</p>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">{t.noPublicParticipationDesc}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}