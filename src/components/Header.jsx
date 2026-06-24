import cpflLogo from "../assets/cpfl.png";

function Header({
  edition,
  activeEdition,
  hasPreviousEdition,
  hasNextEdition,
  onPreviousEdition,
  onNextEdition,
  onOpenHistory,
}) {
  return (
    <header className="rounded-3xl bg-[#2b3f56] p-6 text-white shadow-lg">
      <div className="mb-6 flex items-center justify-between rounded-2xl bg-white/10 px-5 py-3">
        <button
          disabled={!hasPreviousEdition}
          onClick={onPreviousEdition}
          className="text-xs font-bold text-slate-200 disabled:text-slate-500 disabled:cursor-not-allowed"
        >
          ← Anterior
        </button>

        <div className="flex items-center gap-3">
          <div className="text-sm font-semibold text-white">
            Semana monitorada · {edition.period || edition.month}
          </div>

          <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-slate-200">
            {activeEdition?.label}
          </span>

          <button
            type="button"
            onClick={onOpenHistory}
            className="rounded-full bg-white px-4 py-2 text-xs font-bold text-[#2b3f56] shadow-sm transition hover:bg-slate-100 hover:shadow-md"
          >
            Ver histórico 📅
          </button>
        </div>

        <button
          disabled={!hasNextEdition}
          onClick={onNextEdition}
          className="text-xs font-bold text-slate-200 disabled:text-slate-500 disabled:cursor-not-allowed"
        >
          Próxima →
        </button>
      </div>

      <div className="grid grid-cols-[1fr_220px] gap-8">
        <div>
          <div className="text-[10px] uppercase tracking-[0.3em] text-slate-300">
            REGDESK
          </div>

          <h1 className="twcen mt-2 text-[28px] font-semibold tracking-tight text-white">
            Painel de Inteligência Regulatória
          </h1>

          <p className="mt-2 max-w-5xl text-sm leading-relaxed text-slate-200">
            Monitoramento executivo dos principais sinais regulatórios,
            institucionais e de mercado do setor elétrico.
          </p>

          <div className="mt-5 grid max-w-5xl grid-cols-4 gap-3">
            {[
              ["Destaques", edition.highlights?.length || 0, "bg-amber-400"],
              ["Normativos", edition.publishedRules?.length || 0, "bg-red-400"],
              ["Leilões", edition.auctions?.length || 0, "bg-emerald-400"],
              ["Eventos", edition.agenda?.events?.length || 0, "bg-slate-300"],
            ].map(([label, value, color]) => (
              <div
                key={label}
                className="rounded-2xl bg-white/10 px-4 py-3"
              >
                <div className="flex items-center gap-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${color}`}></div>
                  <p className="text-xl font-bold text-white">{value}</p>
                </div>

                <p className="mt-1 text-[11px] font-medium text-slate-300">
                  {label}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col items-end text-right">
          <p className="text-[10px] uppercase tracking-[0.25em] text-slate-300">
            Preparado para
          </p>

          <img
            src={cpflLogo}
            alt="CPFL Energia"
            className="mt-3 h-20 object-contain"
          />

          <div className="mt-5 text-right">
            <p className="text-[9px] uppercase tracking-[0.2em] text-slate-400">
              Última atualização
            </p>

            <p className="mt-1 text-xs font-semibold text-slate-200">
              {edition.updatedAt || "Atualização não informada"}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;