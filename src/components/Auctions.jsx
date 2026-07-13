import ItemCard from "./ItemCard";

export default function Auctions({ data = [], onViewAll, onOpenItem, t }) {
  return (
    <div className="flex h-[360px] flex-col rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">07</div>
          <h2 className="font-heading text-base text-slate-800">{t.auctions}</h2>
        </div>

        <button type="button" onClick={onViewAll} className="font-heading text-xs text-[#3f5b70] hover:underline">
          {t.viewAll}
        </button>
      </div>

      <div id="auctions" className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {data.map((auction, index) => (
          <ItemCard
            key={`${auction.title}-${index}`}
            item={auction}
            onClick={() => onOpenItem?.(auction)}
            footerLeft={auction.agency || "MME"}
            openLabel={t.open}
          />
        ))}

        {data.length === 0 && <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-400">{t.noAuctions}</div>}
      </div>
    </div>
  );
}
