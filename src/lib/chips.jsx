// Lógica compartilhada de "chips" (badges) usada nos cards e nos modais "ler mais".
// - Nos cards: um único chip principal (getPrimaryChip / CardChip).
// - Nos modais: todos os chips disponíveis (getChips / ChipList).

const NEUTRAL = "border-slate-200 bg-slate-100 text-slate-600";

export function badgeClass(value) {
  if (["Crítica", "Crítico", "Critical"].includes(value))
    return "border-red-200 bg-red-100 text-red-700";

  if (["Alta", "Alto", "High"].includes(value))
    return "border-orange-200 bg-orange-100 text-orange-700";

  if (["Média", "Médio", "Medium"].includes(value))
    return "border-amber-200 bg-amber-100 text-amber-700";

  if (["Em andamento", "In progress", "Aberta", "Open", "Em acompanhamento", "Under monitoring"].includes(value))
    return "border-blue-200 bg-blue-100 text-blue-700";

  if (["Iniciado", "Started"].includes(value))
    return "border-purple-200 bg-purple-100 text-purple-700";

  if (["Concluído", "Completed"].includes(value))
    return "border-emerald-200 bg-emerald-100 text-emerald-700";

  // Normativos
  if (["Publicado", "Published"].includes(value))
    return "border-emerald-200 bg-emerald-100 text-emerald-700";

  if (["Aguardando publicação", "Pending publication", "Aprovado pendente de publicação", "Approved pending publication"].includes(value))
    return "border-amber-200 bg-amber-100 text-amber-700";

  if (["Esperado", "Expected", "Previsto", "Agendado", "Scheduled"].includes(value))
    return "border-blue-200 bg-blue-100 text-blue-700";

  if (["Revogado", "Revoked", "Encerrada", "Closed"].includes(value))
    return "border-red-200 bg-red-100 text-red-700";

  // Tipos de reunião/pauta (Pauta ANEEL) — categoria própria
  if (/reuni|circuito|delibera|meeting|board|voting session/i.test(value))
    return "border-indigo-200 bg-indigo-100 text-indigo-700";

  return NEUTRAL;
}

// Chip principal (o único que aparece no card da homepage).
export function getPrimaryChip(item) {
  return item.status || item.level || item.impact || item.type || "";
}

// Todos os chips disponíveis (para o modal "ler mais").
export function getChips(item, t) {
  const chips = [];
  const add = (label, value, colored = false) => {
    const v = (value ?? "").toString().trim();
    if (!v) return;
    chips.push({ label, value: v, className: colored ? badgeClass(v) : NEUTRAL });
  };

  add(t.status, item.status, true);
  add(t.criticality, item.level || item.impact, true);
  add(t.type, item.type, false);
  add(t.number, item.number || item.referenceNumber, false);
  add(t.deadline, item.deadline, false);
  add(t.date, item.date, false);
  add(t.agency, item.agency, false);

  return chips;
}

// Chip único do card. `className` controla o posicionamento (ex.: absolute).
export function CardChip({ item, className = "" }) {
  const value = getPrimaryChip(item);
  if (!value) return null;
  return (
    <span
      className={`max-w-[130px] truncate rounded-full border px-2 py-1 text-[9px] font-bold ${badgeClass(
        value
      )} ${className}`}
    >
      {value}
    </span>
  );
}

// Lista completa de chips para os modais.
export function ChipList({ item, t, className = "" }) {
  const chips = getChips(item, t);
  if (!chips.length) return null;
  return (
    <div className={`flex flex-wrap gap-2 text-xs ${className}`}>
      {chips.map((chip, i) => (
        <span
          key={`${chip.label}-${i}`}
          className={`font-body rounded-full border px-2 py-1 ${chip.className}`}
        >
          <span className="opacity-60">{chip.label}:</span> {chip.value}
        </span>
      ))}
    </div>
  );
}
