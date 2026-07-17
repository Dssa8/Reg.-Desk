// Barra de navegação de edição — usada no header da homepage e no header das
// páginas "ver tudo", para manter total consistência entre as duas.
export default function EditionBar({
  edition,
  activeEdition,
  hasPreviousEdition,
  hasNextEdition,
  onPreviousEdition,
  onNextEdition,
  onOpenHistory,
  language,
  onChangeLanguage,
  t,
}) {
  const langButton = (lang) =>
    `font-heading rounded-full px-3.5 py-1.5 text-[13px] transition ${
      language === lang
        ? "bg-[#86A876] text-[#021A34] shadow-sm"
        : "text-slate-200 hover:bg-white/10 hover:text-white"
    }`;

  return (
    <div className="grid grid-cols-[auto_1fr_auto] items-center gap-4 rounded-2xl border border-white/5 bg-white/10 px-3 py-1.5">
      <div className="flex items-center gap-2.5 justify-self-start">
        <span className="font-heading whitespace-nowrap rounded-full bg-[#86A876] px-3.5 py-1.5 text-[13px] text-[#021A34]">
          {activeEdition?.label}
        </span>

        <button
          type="button"
          onClick={onOpenHistory}
          className="font-heading whitespace-nowrap rounded-full bg-white px-3.5 py-1.5 text-[13px] text-[#021A34] shadow-sm transition hover:bg-slate-100 hover:shadow-md"
        >
          {t.viewHistory}
        </button>
      </div>

      <div className="flex items-center justify-center gap-3 justify-self-center">
        <button
          type="button"
          aria-label={t.previous}
          disabled={!hasPreviousEdition}
          onClick={onPreviousEdition}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/10 text-[16px] leading-none text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-white/10"
        >
          ‹
        </button>

        <span className="font-card-title whitespace-nowrap text-[14px] text-white">
          {t.monitoredWeek} · {edition.period || edition.month}
        </span>

        <button
          type="button"
          aria-label={t.next}
          disabled={!hasNextEdition}
          onClick={onNextEdition}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/10 text-[16px] leading-none text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-white/10"
        >
          ›
        </button>
      </div>

      <div className="justify-self-end">
        <div className="flex rounded-full bg-white/10 p-1">
          <button type="button" onClick={() => onChangeLanguage("pt")} className={langButton("pt")}>
            {t.languagePt}
          </button>

          <button type="button" onClick={() => onChangeLanguage("en")} className={langButton("en")}>
            {t.languageEn}
          </button>
        </div>
      </div>
    </div>
  );
}
