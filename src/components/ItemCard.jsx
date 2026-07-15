import { CardChip } from "../lib/chips";

// Superfície do card:
// - "panel": card dentro de um painel branco (fundo levemente cinza).
// - "page": card direto sobre o fundo da página (fundo branco com sombra).
const SURFACE = {
  panel: "bg-slate-50/60 hover:bg-white hover:shadow-sm",
  page: "bg-white shadow-sm hover:-translate-y-1 hover:shadow-md",
};

// Card padrão usado em TODAS as seções e páginas, com a mesma hierarquia e
// tamanhos de fonte dos cards de "Participação Pública".
export default function ItemCard({
  item,
  onClick,
  openLabel = "Abrir",
  deadlineLabel = "Prazo",
  footerLeft,
  surface = "panel",
  height = "h-[145px]",
}) {
  const description = item.detail || item.summary || item.subtitle;
  const left = footerLeft ?? item.agency ?? "RegDesk";

  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative flex ${height} w-full flex-col rounded-2xl border border-slate-100 p-3 text-left transition ${SURFACE[surface]}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-heading line-clamp-2 min-w-0 flex-1 text-[13px] font-semibold leading-tight text-slate-800">
          {item.title}
        </h3>

        <CardChip item={item} className="mt-0.5 shrink-0" />
      </div>

      {description && (
        <p className="font-body mt-2.5 line-clamp-2 text-[12px] leading-relaxed text-slate-600">
          {description}
        </p>
      )}

      <div className="mt-auto flex items-center justify-between gap-2 border-t border-slate-100 pt-2">
        <span className="font-body truncate text-[11px] font-semibold text-slate-400">{left}</span>

        <div className="flex shrink-0 items-center gap-3">
          {item.date && (
            <span className="font-body text-[11px] font-semibold text-slate-500">{item.date}</span>
          )}
          {item.deadline && (
            <span className="font-body text-[11px] font-semibold text-slate-500">
              <span className="font-normal text-slate-400">{deadlineLabel}:</span> {item.deadline}
            </span>
          )}
          <span className="font-heading text-xs text-[#3f5b70]">{openLabel}</span>
        </div>
      </div>
    </button>
  );
}
