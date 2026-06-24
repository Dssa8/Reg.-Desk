export default function Agenda({ data }) {
  const days = data?.days || [];
const eventDays = data?.eventDays || [];
const events = data?.events || [];
const month = data?.month || "";

  return (
    <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 hover:shadow-md transition">

      {/* HEADER */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center text-sm font-bold">
            06
          </div>

          <h2 className="text-xl font-bold text-slate-800">
            Agenda
          </h2>
        </div>

        <span className="text-sm text-slate-500">
          {month}
        </span>
      </div>

      {/* WEEK HEADER */}
      <div className="grid grid-cols-7 text-center text-xs font-semibold text-slate-400 mb-3">
        <div>M</div>
        <div>T</div>
        <div>W</div>
        <div>T</div>
        <div>F</div>
        <div>S</div>
        <div>S</div>
      </div>

      {/* CALENDAR */}
      <div className="grid grid-cols-7 gap-2">
        {days.map((day, index) => (
          <div
            key={index}
            className={`
              h-10
              rounded-xl
              flex
              items-center
              justify-center
              text-sm
              transition
              ${
                eventDays.includes(day)
                  ? "bg-slate-800 text-white font-bold"
                  : "bg-slate-50 text-slate-600 hover:bg-white hover:shadow-sm"
              }
            `}
          >
            {day}
          </div>
        ))}
      </div>

      {/* EVENTS LIST */}
<div className="mt-5 border-t border-slate-100 pt-4 space-y-2">
  {events.map((event) => (
    <div
      key={`${event.title}-${event.date}`}
      className="flex items-center gap-2 text-sm text-slate-700"
    >
      <div className="w-2.5 h-2.5 rounded-full bg-slate-800"></div>
      <span>
        {event.title} — {event.date}
      </span>
    </div>
  ))}
</div>

</div>
);
}