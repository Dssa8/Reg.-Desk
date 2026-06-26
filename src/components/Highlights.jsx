import { useState } from "react";

function levelStyle(level) {
  if (level === "Crítica" || level === "Crítico")
    return "bg-red-100 text-red-700 border-red-200";

  if (level === "Alta" || level === "Alto")
    return "bg-orange-100 text-orange-700 border-orange-200";

  if (level === "Média" || level === "Médio")
    return "bg-amber-100 text-amber-700 border-amber-200";

  return "bg-emerald-100 text-emerald-700 border-emerald-200";
}

export default function Highlights({ data = [], onViewAll }) {
  const [selected, setSelected] = useState(null);

  return (
    <div className="mt-6" id="highlights">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
            01
          </div>

          <h2 className="text-base font-semibold text-slate-800">
            Destaques da Semana
          </h2>
        </div>

        <button
          onClick={onViewAll}
          className="text-xs font-bold text-[#3f5b70] hover:underline"
        >
          Ver tudo →
        </button>
      </div>

      {data.length === 0 ? (
        <div className="rounded-3xl border border-slate-100 bg-white p-10 text-center text-sm text-slate-500">
          Nenhum destaque disponível no momento.
        </div>
      ) : (
        <div className="grid items-stretch gap-4 md:grid-cols-3">
          {data.map((item, idx) => (
            <button
              key={`${item.title}-${idx}`}
              onClick={() => setSelected(item)}
              className="
                flex min-h-[140px] flex-col rounded-3xl border border-slate-100
                bg-white p-3 text-left shadow-sm transition-all duration-200
                hover:-translate-y-1 hover:shadow-md
              "
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-[13px] font-semibold leading-snug text-slate-800">
                  {item.title}
                </h3>

                {item.level && (
                  <span
                    className={`shrink-0 rounded-full border px-2 py-1 text-[9px] font-bold ${levelStyle(
                      item.level
                    )}`}
                  >
                    {item.level}
                  </span>
                )}
              </div>

              {(item.detail || item.summary) && (
                <p className="mt-2 line-clamp-3 text-[12px] leading-relaxed text-slate-600">
                  {item.detail || item.summary}
                </p>
              )}

              <div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-2">
                <span className="text-[11px] font-semibold text-slate-400">
                  Análise FSET
                </span>

                <span className="text-xs font-bold text-[#3f5b70]">
                  Abrir →
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-800">
                  {selected.title}
                </h3>

                <div className="mt-3 flex flex-wrap gap-2">
                  {selected.level && (
                    <span
                      className={`rounded-full border px-2 py-1 text-xs font-semibold ${levelStyle(
                        selected.level
                      )}`}
                    >
                      {selected.level}
                    </span>
                  )}

                  {selected.agency && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                      {selected.agency}
                    </span>
                  )}

                  {selected.deadline && (
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                      Prazo: {selected.deadline}
                    </span>
                  )}
                </div>
              </div>

              <button
                onClick={() => setSelected(null)}
                className="text-sm font-bold text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            {selected.detail ? (
              <p className="mt-5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
                {selected.detail}
              </p>
            ) : (
              <p className="mt-5 text-sm leading-relaxed text-slate-600">
                Texto completo não informado.
              </p>
            )}

            {selected.link && (
              <a
                href={selected.link}
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