import { useState } from "react";

import { ChipList } from "../lib/chips";
import ItemCard from "./ItemCard";

export default function Highlights({ data = [], onViewAll, t }) {
  const [selected, setSelected] = useState(null);

  return (
    <div className="mt-6" id="highlights">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
            01
          </div>

          <h2 className="font-heading text-base text-slate-800">{t.highlights}</h2>
        </div>

        <button onClick={onViewAll} className="font-heading text-xs text-[#3f5b70] hover:underline">
          {t.viewAll}
        </button>
      </div>

      {data.length === 0 ? (
        <div className="rounded-3xl border border-slate-100 bg-white p-10 text-center text-sm text-slate-500">
          {t.noHighlights}
        </div>
      ) : (
        <div className="grid items-stretch gap-4 md:grid-cols-3">
          {data.map((item, idx) => (
            <ItemCard
              key={`${item.title}-${idx}`}
              item={item}
              onClick={() => setSelected(item)}
              surface="page"
              footerLeft={t.analysisFset}
              openLabel={t.open}
            />
          ))}
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-heading text-lg text-slate-800">{selected.title}</h3>

                <ChipList item={selected} t={t} className="mt-3" />
              </div>

              <button onClick={() => setSelected(null)} className="text-sm font-bold text-slate-400 hover:text-slate-700">✕</button>
            </div>

            {selected.detail ? (
              <p className="font-body mt-5 whitespace-pre-line text-sm leading-relaxed text-slate-600">{selected.detail}</p>
            ) : (
              <p className="font-body mt-5 text-sm leading-relaxed text-slate-600">{t.textMissing}</p>
            )}

            {selected.link && (
              <a href={selected.link} target="_blank" rel="noreferrer" className="font-heading mt-6 inline-block text-sm text-[#3f5b70]">
                {t.openSource}
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
