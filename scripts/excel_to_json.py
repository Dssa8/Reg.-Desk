import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta

INPUT_FILE = Path("input/modelo_report_regdesk_pt.xlsx")
OUTPUT_DIR = Path("src/data")

MONTHS_PT = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro",
}


def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_active(value):
    if pd.isna(value):
        return False
    if value is True:
        return True
    return str(value).strip().lower() in ["true", "1", "sim", "yes"]


def parse_date(value):
    if pd.isna(value) or value == "":
        return None

    if isinstance(value, datetime):
        return value

    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


def format_date(value):
    date = parse_date(value)
    if date is None:
        return clean(value)

    return date.strftime("%d/%m/%Y")


def format_datetime(value):
    date = parse_date(value)
    if date is None:
        return clean(value)

    return date.strftime("%d/%m/%Y às %H:%M")


def format_month(value):
    date = parse_date(value)
    if date is None:
        return ""

    return f"{MONTHS_PT[date.month].capitalize()} {date.year}"


def format_edition_number(value):
    if pd.isna(value):
        return ""

    try:
        return f"{int(value):03d}"
    except Exception:
        return clean(value)


def build_calendar_days(reference_date):
    first_day = reference_date.replace(day=1)
    blanks = first_day.weekday()

    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1, day=1)

    days_in_month = (next_month - timedelta(days=1)).day

    return [""] * blanks + [str(day) for day in range(1, days_in_month + 1)]


def main():
    conteudos = pd.read_excel(INPUT_FILE, sheet_name="Conteudos")
    edicoes = pd.read_excel(INPUT_FILE, sheet_name="Edicoes")
    secoes = pd.read_excel(INPUT_FILE, sheet_name="Secoes")
    opcoes = pd.read_excel(INPUT_FILE, sheet_name="Opcoes")
    orgaos = pd.read_excel(INPUT_FILE, sheet_name="Orgaos")

    secao_map = dict(zip(secoes["id"], secoes["slug"]))
    orgao_map = dict(zip(orgaos["id"], orgaos["sigla"]))

    option_map = {}
    for _, row in opcoes.iterrows():
        grupo = clean(row.get("grupo"))
        code = clean(row.get("code"))
        label = clean(row.get("label_pt"))

        if grupo and code:
            option_map[(grupo, code)] = label

    edicao = edicoes.iloc[0]
    data_edicao = parse_date(edicao["data_edicao"])

    if data_edicao is None:
        raise ValueError("Data da edição não encontrada na aba Edicoes")

    edition_date = data_edicao.strftime("%Y-%m-%d")
    edition_number = format_edition_number(edicao.get("numero_edicao"))

    period_start = format_date(edicao.get("periodo_inicio"))
    period_end = format_date(edicao.get("periodo_fim"))

    period = f"{period_start} a {period_end}" if period_start and period_end else ""
    updated_at = format_datetime(edicao.get("updated_at"))

    result = {
        "edition": edition_date,
        "editionNumber": edition_number,
        "editionId": f"cpfl-{edition_number}" if edition_number else "",
        "client": "CPFL Energia",
        "title": clean(edicao.get("titulo_pt")),
        "summary": clean(edicao.get("resumo_pt")),
        "month": format_month(data_edicao),
        "periodStart": period_start,
        "periodEnd": period_end,
        "period": period,
        "updatedAt": updated_at,

        "highlights": [],
        "aneelAgenda": [],
        "publishedRules": [],
        "aneelTopics": [],
        "mmeTopics": [],
        "publicParticipation": [],
        "auctions": [],

        "agenda": {
            "month": format_month(data_edicao),
            "days": build_calendar_days(data_edicao),
            "eventDays": [],
            "events": [],
        },
    }

    conteudos = conteudos.sort_values(by="ordem", na_position="last")

    for _, row in conteudos.iterrows():
        if not is_active(row.get("ativo")):
            continue

        title = clean(row.get("titulo_pt"))
        if not title:
            continue

        secao_slug = secao_map.get(row.get("secao_id"), "")
        orgao = orgao_map.get(row.get("orgao_id"), "")

        status_code = clean(row.get("status_code"))
        criticidade_code = clean(row.get("criticidade_code"))
        mudanca_code = clean(row.get("mudanca_code"))
        subtipo_code = clean(row.get("subtipo_code"))
        data_precisao_code = clean(row.get("data_precisao_code"))

        status_label = (
            option_map.get(("status_regulatorio", status_code))
            or option_map.get(("status_consulta", status_code))
            or option_map.get(("status_leilao", status_code))
            or option_map.get(("status_normativo", status_code))
            or status_code
        )

        criticidade_label = option_map.get(
            ("criticidade", criticidade_code),
            criticidade_code,
        )

        mudanca_label = option_map.get(
            ("mudanca", mudanca_code),
            mudanca_code,
        )

        subtipo_label = option_map.get(
            ("subtipo_conteudo", subtipo_code),
            subtipo_code,
        )

        data_precisao_label = option_map.get(
            ("data_precisao", data_precisao_code),
            data_precisao_code,
        )

        item_base = {
            "title": title,
            "summary": clean(row.get("resumo_pt")),
            "detail": clean(row.get("detalhe_pt")),
            "agency": orgao,
            "status": status_label,
            "level": criticidade_label,
            "change": mudanca_label,
            "deadline": format_date(row.get("prazo_data")),
            "date": format_date(row.get("data_evento")),
            "datePrecision": data_precisao_label,
            "type": subtipo_label,
            "referenceNumber": clean(row.get("numero_referencia")),
            "number": clean(row.get("numero_referencia")),
            "link": clean(row.get("link_referencia")),
        }

        if secao_slug == "destaques-da-semana":
            result["highlights"].append(item_base)

        elif secao_slug == "pauta-aneel":
            result["aneelAgenda"].append(item_base)

        elif secao_slug == "normativos-publicados":
            result["publishedRules"].append(item_base)

        elif secao_slug == "pendencias-regulatorias-aneel":
            result["aneelTopics"].append(item_base)

        elif secao_slug == "pendencias-regulatorias-mme":
            result["mmeTopics"].append(item_base)

        elif secao_slug == "temas-abertos-participacao-publica":
            result["publicParticipation"].append(item_base)

        elif secao_slug == "cronograma-proximos-leiloes":
            result["auctions"].append(item_base)

        elif secao_slug == "agenda-institucional":
            event_date = parse_date(row.get("data_evento"))
            formatted = format_date(row.get("data_evento"))

            result["agenda"]["events"].append(
                {
                    "title": title,
                    "date": formatted,
                    "agency": orgao,
                    "type": subtipo_label,
                    "link": clean(row.get("link_referencia")),
                }
            )

            if event_date is not None:
                day = str(event_date.day)
                if day not in result["agenda"]["eventDays"]:
                    result["agenda"]["eventDays"].append(day)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"edition-{edition_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"JSON criado com sucesso: {output_file}")


if __name__ == "__main__":
    main()