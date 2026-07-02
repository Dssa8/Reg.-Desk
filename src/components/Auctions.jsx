export default function Auctions({ data = [], onViewAll, onOpenItem, t }) {
  return (
    <div className="flex h-[420px] flex-col rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">07</div>
          <h2 className="text-base font-semibold text-slate-800">{t.auctions}</h2>
        </div>

        <button type="button" onClick={onViewAll} className="text-xs font-bold text-[#3f5b70] hover:underline">
          {t.viewAll}
        </button>
      </div>

      <div id="auctions" className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {data.map((auction, index) => (
          <button key={`${auction.title}-${index}`} type="button" onClick={() => onOpenItem?.(auction)} className="w-full rounded-2xl border border-slate-100 bg-slate-50/60 p-2.5 text-left transition hover:bg-white hover:shadow-sm">
            <h3 className="text-[13px] font-semibold leading-tight text-slate-800">{auction.title}</h3>
            {auction.detail && <p className="mt-0.5 line-clamp-2 text-[12px] leading-relaxed text-slate-600">{auction.detail}</p>}

            <div className="mt-2 flex items-center justify-between border-t border-slate-100 pt-2">
              <span className="text-[11px] font-semibold text-slate-400">{auction.agency || "MME"}</span>
              <span className="text-xs font-bold text-[#3f5b70]">{t.open}</span>
            </div>
          </button>
        ))}

        {data.length === 0 && <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-400">{t.noAuctions}</div>}
      </div>
    </div>
  );
}
