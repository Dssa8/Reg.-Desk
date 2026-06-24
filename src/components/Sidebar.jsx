import { useEffect, useState } from "react";

export default function Sidebar({ agenda }) {
  const items = [
    ["highlights", "01", "Destaques", "bg-amber-500"],
    ["aneel-agenda", "02", "Pautas ANEEL", "bg-blue-500"],
    ["published-rules", "03", "Normativos publicados", "bg-cyan-500"],
    ["aneel", "04", "Temas ANEEL", "bg-violet-500"],
    ["mme", "05", "Temas MME", "bg-emerald-500"],
    ["auctions", "06", "Leilões", "bg-slate-400"],
  ];

  const [active, setActive] = useState("highlights");
  const [selectedDay, setSelectedDay] = useState(null);

  const handleScroll = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  useEffect(() => {
    const handleScrollSpy = () => {
      let current = "highlights";

      for (const [id] of items) {
        const section = document.getElementById(id);
        if (!section) continue;

        const rect = section.getBoundingClientRect();
        if (rect.top <= 120) current = id;
      }

      setActive(current);
    };

    window.addEventListener("scroll", handleScrollSpy);
    return () => window.removeEventListener("scroll", handleScrollSpy);
  }, []);

  const days = agenda?.days || [];
  const events = agenda?.events || [];
  const eventDays = agenda?.eventDays || [];

  const getDayFromDate = (date) => {
    if (!date) return "";
    return String(Number(date.split("/")[0]));
  };

  const calculatedEventDays = events
    .map((event) => getDayFromDate(event.date))
    .filter(Boolean);

  const allEventDays = [...new Set([...eventDays, ...calculatedEventDays])];

  const selectedEvents = selectedDay
    ? events.filter((event) => getDayFromDate(event.date) === selectedDay)
    : [];

  return (
    <aside className="w-80 min-h-screen bg-[#2b3f56] text-white p-6 flex flex-col">
      <div>
        <h2 className="twcen text-4xl font-extrabold tracking-tight">REGDESK</h2>

        <p className="mt-1 text-[10px] uppercase tracking-[0.3em] text-slate-300">
          Inteligência Regulatória
        </p>
      </div>

      <nav className="mt-10 space-y-2">
        {items.map(([id, number, label, color]) => (
          <button
            key={id}
            onClick={() => handleScroll(id)}
            className={`
              w-full flex items-center gap-3 px-3 py-3 rounded-2xl text-left transition
              ${active === id ? "bg-white/15 shadow-md" : "hover:bg-white/10"}
            `}
          >
            <div
              className={`h-8 w-8 shrink-0 rounded-xl flex items-center justify-center text-[11px] font-bold text-white ${color}`}
            >
              {number}
            </div>

            <span className="text-sm font-medium leading-snug">{label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center justify-between">
          <p className="text-[10px] uppercase tracking-widest text-slate-300">
            Agenda
          </p>

          <span className="text-xs font-bold text-slate-200">
            {agenda?.month}
          </span>
        </div>

        <div className="mt-4 grid grid-cols-7 gap-1 text-center text-[10px] font-bold text-slate-300">
          <div>S</div>
          <div>T</div>
          <div>Q</div>
          <div>Q</div>
          <div>S</div>
          <div>S</div>
          <div>D</div>
        </div>

        <div className="mt-2 grid grid-cols-7 gap-1">
          {days.map((day, index) => {
            const hasEvent = allEventDays.includes(day);
            const isSelected = selectedDay === day;

            return (
              <button
                key={`${day}-${index}`}
                disabled={!day}
                onClick={() => hasEvent && setSelectedDay(day)}
                className={`
                  h-7 rounded-lg flex items-center justify-center text-[11px] transition
                  ${
                    isSelected
                      ? "bg-amber-400 text-[#2b3f56] font-bold"
                      : hasEvent
                      ? "bg-white text-[#2b3f56] font-bold hover:bg-amber-100"
                      : day
                      ? "bg-white/10 text-slate-200"
                      : "bg-transparent"
                  }
                `}
              >
                {day}
              </button>
            );
          })}
        </div>

        <div className="mt-4 space-y-2">
          {selectedDay ? (
            selectedEvents.length > 0 ? (
              selectedEvents.map((event, index) => (
                <div
                  key={`${event.title}-${index}`}
                  className="rounded-2xl bg-white/10 p-3"
                >
                  <p className="text-xs font-bold text-white line-clamp-2">
                    {event.title}
                  </p>

                  <p className="mt-1 text-[10px] text-slate-300">
                    {event.date || event.agency || "Evento institucional"}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-300">
                Nenhum evento neste dia.
              </p>
            )
          ) : (
            <p className="text-xs text-slate-300">
              Clique em um dia destacado para ver os eventos.
            </p>
          )}
        </div>
      </div>

      <div className="mt-auto rounded-3xl border border-white/10 bg-white/5 p-4">
        <p className="text-[10px] uppercase tracking-widest text-slate-300">
          Visão FSET
        </p>

        <p className="mt-2 text-xs leading-relaxed text-slate-300">
          Monitoramento executivo de sinais regulatórios, institucionais e de
          mercado para apoiar decisões estratégicas.
        </p>
      </div>
    </aside>
  );
}