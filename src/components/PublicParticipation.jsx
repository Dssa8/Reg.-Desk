export default function PublicParticipation({ data = [] }) {
  const impactColor = (impact) => {
    if (impact === "Alta" || impact === "Alto") {
      return "bg-red-100 text-red-700";
    }

    if (impact === "Crítica" || impact === "Crítico") {
      return "bg-red-100 text-red-700";
    }

    return "bg-amber-100 text-amber-700";
  };

  return (
    <div id="consultations" className="bg-white rounded-3xl shadow p-6">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center text-sm font-bold">
            04
          </div>

          <h2 className="text-lg font-bold">
            Consultas Públicas
          </h2>
        </div>

        <button className="text-sm font-semibold text-slate-500 hover:text-slate-700">
          Ver tudo →
        </button>
      </div>

      <div className="space-y-3">
        {data.map((item) => (
          <div
            key={item.title}
            className="
              rounded-2xl
              border
              border-slate-100
              bg-slate-50
              p-4
              hover:bg-white
              hover:shadow-sm
              transition
              cursor-pointer
            "
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-bold text-sm text-slate-800">
                  {item.title}
                </h3>

                <p className="mt-1 text-sm text-slate-600">
                  {item.subtitle}
                </p>
              </div>

              <span
                className={`text-xs px-2 py-1 rounded-full font-semibold ${impactColor(
                  item.impact
                )}`}
              >
                {item.impact}
              </span>
            </div>

            <div className="mt-3 text-xs text-slate-500">
              Prazo: {item.deadline}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}