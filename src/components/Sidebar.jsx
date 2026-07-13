import { useState } from "react";
import logo from "../assets/cropped_logo.png";
import fsetLogo from "../assets/fset.png";

export default function Sidebar({
  agenda,
  t,
  onNavigate,
  activePage = "dashboard",
  clientName,
  onLogout,
}) {
  const items = [
  ["highlights", "01", t.highlights],
  ["aneel-agenda", "02", t.aneelAgenda],
  ["published-rules", "03", t.publishedRules],
  ["aneel", "04", t.aneelTopics],
  ["mme", "05", t.mmeTopics],
  ["public-participation", "06", t.publicParticipation],
  ["auctions", "07", t.auctions],
];

  const [selectedDay, setSelectedDay] = useState(null);

  const handleNavigate = (id) => {
    onNavigate?.(id);
  };

  const days = agenda?.days || [];
  const events = agenda?.events || [];
  const eventDays = agenda?.eventDays || [];

  const getDayFromDate = (date) => {
    if (!date) return "";
    return String(Number(String(date).split("/")[0]));
  };

  const eventHasDay = (event, day) => {
    const directDate = getDayFromDate(event.date);
    const displayDates = event.displayDates || [];

    return (
      directDate === day ||
      displayDates.some((date) => getDayFromDate(date) === day)
    );
  };

  const calculatedEventDays = events
    .flatMap((event) => [event.date, ...(event.displayDates || [])])
    .map((date) => getDayFromDate(date))
    .filter(Boolean);

  const allEventDays = [...new Set([...eventDays, ...calculatedEventDays])];

  const selectedEvents = selectedDay
    ? events.filter((event) => eventHasDay(event, selectedDay))
    : [];

  return (
    <aside className="flex min-h-screen w-80 flex-col bg-[#2b3f56] px-5 py-6 text-white">
      <div className="flex items-center gap-3 px-2">
        <img src={logo} alt="RegDesk" className="h-10 w-auto shrink-0 object-contain" />

        <div className="min-w-0">
          <h2 className="font-heading relative top-[8px] text-[27px] leading-none tracking-tight text-white">
            REGDESK
          </h2>

          <p className="font-body mt-1.5 text-[9px] uppercase tracking-[0.2em] text-slate-400">
            {t.sidebarTagline}
          </p>
        </div>
      </div>

      <nav className="mt-8 space-y-1">
        {items.map(([id, number, label]) => (
          <button
            key={id}
            onClick={() => handleNavigate(id)}
            className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
              activePage === id ? "bg-white/15" : "hover:bg-white/10"
            }`}
          >
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[12px] font-bold transition ${
                activePage === id
                  ? "bg-white text-[#2b3f56]"
                  : "bg-[#9FBE86] text-white group-hover:bg-[#adca97]"
              }`}
            >
              {number}
            </div>

            <span
              className={`font-heading text-[15px] leading-tight transition ${
                activePage === id ? "text-white" : "text-slate-200 group-hover:text-white"
              }`}
            >
              {label}
            </span>
          </button>
        ))}
      </nav>

      <div className="mt-7 rounded-3xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-baseline justify-between">
          <p className="font-heading text-[11px] uppercase tracking-[0.22em] text-slate-400">
            {t.agendaLabel}
          </p>

          <span className="font-card-title text-[13px] text-slate-100">
            {agenda?.month}
          </span>
        </div>

        <div className="mt-4 grid grid-cols-7 gap-1 text-center">
          {t.weekdays.map((day, index) => (
            <div
              key={`${day}-${index}`}
              className="font-heading text-[10px] uppercase tracking-wide text-slate-400"
            >
              {day}
            </div>
          ))}
        </div>

        <div className="mt-1.5 grid grid-cols-7 gap-1">
          {days.map((day, index) => {
            const hasEvent = allEventDays.includes(day);
            const isSelected = selectedDay === day;

            return (
              <button
                key={`${day}-${index}`}
                disabled={!day}
                onClick={() => hasEvent && setSelectedDay(day)}
                className={`font-body flex aspect-square items-center justify-center rounded-lg text-[13px] transition ${
                  isSelected
                    ? "bg-[#9FBE86] font-semibold text-white"
                    : hasEvent
                    ? "bg-white font-semibold text-[#2b3f56] hover:bg-[#adca97] hover:text-white"
                    : day
                    ? "text-slate-300 hover:bg-white/10"
                    : "bg-transparent"
                }`}
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
                  <p className="font-card-title line-clamp-2 text-[13px] leading-snug text-white">
                    {event.title}
                  </p>

                  <p className="font-body mt-1 text-[11px] text-slate-300">
                    {event.date ||
                      event.recurrenceDescription ||
                      event.agency ||
                      t.institutionalEvent}
                  </p>
                </div>
              ))
            ) : (
              <p className="font-body text-[12px] leading-relaxed text-slate-400">
                {t.noEventOnDay}
              </p>
            )
          ) : (
            <p className="font-body text-[12px] leading-relaxed text-slate-400">
              {t.clickHighlightedDay}
            </p>
          )}
        </div>
      </div>

      <div className="mt-auto pt-6">
        <div className="mb-4 flex justify-center">
          <img src={fsetLogo} alt="FSET" className="h-12 w-auto object-contain" />
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
          <p className="font-heading text-[11px] uppercase tracking-[0.22em] text-slate-400">
            {t.sidebarVisionTitle}
          </p>

          <p className="font-body mt-2 text-[13px] leading-relaxed text-slate-200">
            {t.sidebarVisionText}
          </p>
        </div>

        {clientName && (
          <button
            type="button"
            onClick={onLogout}
            className="mt-4 flex w-full items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left transition hover:bg-white/10"
          >
            <span className="min-w-0">
              <span className="font-body block text-[10px] uppercase tracking-[0.2em] text-slate-400">
                {t.clientLabel}
              </span>
              <span className="font-heading block truncate text-[13px] text-white">
                {clientName}
              </span>
            </span>
            <span className="font-heading shrink-0 text-[12px] text-[#9FBE86]">
              {t.logout}
            </span>
          </button>
        )}
      </div>
    </aside>
  );
}