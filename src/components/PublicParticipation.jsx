export default function PublicParticipation({
  data = [],
  onViewAll,
  onOpenItem,
}) {
  const impactColor = (impact) => {
    if (impact === "Crítica" || impact === "Crítico")
      return "bg-red-100 text-red-700 border-red-200";

    if (impact === "Alta" || impact === "Alto")
      return "bg-orange-100 text-orange-700 border-orange-200";

    if (impact === "Média" || impact === "Médio")
      return "bg-amber-100 text-amber-700 border-amber-200";

    return "bg-slate-100 text-slate-600 border-slate-200";
  };

  return (
    <div
      id="public-participation"
      className="h-[420px] rounded-3xl bg-white p-5 shadow-sm border border-slate-100 flex flex-col"
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[#2b3f56] text-xs font-bold text-white">
            06
          </div>

          <h2 className="text-base font-semibold leading-tight text-slate-800">
            Temas Abertos para Participação Pública
          </h2>
        </div>

        <button
          type="button"
          onClick={onViewAll}
          className="shrink-0 text-xs font-bold text-[#3f5b70] hover:underline"
        >
          Ver tudo →
        </button>
      </div>

      <div className="mt-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {data.length > 0 ? (
          data.map((item, index) => (
            <button
              key={`${item.title}-${index}`}
              type="button"
              onClick={() => onOpenItem?.(item)}
              className="
                flex h-[145px] w-full flex-col rounded-2xl border border-slate-100
                bg-slate-50/60 p-3 text-left transition hover:bg-white hover:shadow-sm
              "
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="line-clamp-2 text-[13px] font-semibold leading-tight text-slate-800">
                  {item.title}
                </h3>

                {(item.impact || item.level) && (
                  <span
                    className={`shrink-0 rounded-full border px-2 py-1 text-[9px] font-bold ${impactColor(
                      item.impact || item.level
                    )}`}
                  >
                    {item.impact || item.level}
                  </span>
                )}
              </div>

              {(item.detail || item.summary || item.subtitle) && (
                <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-slate-600">
                  {item.detail || item.summary || item.subtitle}
                </p>
              )}

              <div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-2">
                <span className="text-[11px] font-semibold text-slate-400">
                  {item.agency || "RegDesk"}
                </span>

                <span className="text-xs font-bold text-[#3f5b70]">
                  Abrir →
                </span>
              </div>
            </button>
          ))
        ) : (
          <div className="flex h-full items-center justify-center rounded-2xl bg-slate-50">
            <div className="px-8 text-center">
              <p className="text-sm font-semibold text-slate-500">
                Nenhum tema cadastrado.
              </p>

              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Os temas aparecerão automaticamente quando forem incluídos na
                database.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}