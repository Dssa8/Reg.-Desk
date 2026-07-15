import ItemCard from "./ItemCard";

export default function Auctions({ data = [], onViewAll, onOpenItem, t }) {
  const auctions = data.filter((item) => item.kind !== "comment");
  const comment = data.find((item) => item.kind === "comment");

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
        {auctions.map((auction, index) => (
          <ItemCard
            key={`${auction.title}-${index}`}
            item={auction}
            onClick={() => onOpenItem?.(auction)}
            footerLeft={auction.agency || "MME"}
            openLabel={t.open}
          />
        ))}

        {auctions.length === 0 && <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-400">{t.noAuctions}</div>}
      </div>

      {comment && (
        <button
          type="button"
          onClick={() => onOpenItem?.(comment)}
          className="group mt-3 w-full shrink-0 border-t border-slate-100 pt-3 text-left"
        >
          <p className="font-heading text-[10px] uppercase tracking-[0.16em] text-[#3f5b70]">
            {comment.type}
          </p>
          <p className="font-body mt-1 line-clamp-2 text-[12px] leading-relaxed text-slate-600 transition group-hover:text-slate-800">
            {comment.detail || comment.summary}
          </p>
        </button>
      )}
    </div>
  );
}
