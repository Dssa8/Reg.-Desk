import json
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

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

MONTHS_EN = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

WEEKDAY_TO_NUMBER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

SHEET_NAMES = {
    "edicoes": ["01_edicoes", "Edicoes"],
    "secoes": ["02_secoes", "Secoes"],
    "orgaos": ["03_orgaos", "Orgaos"],
    "destaques": ["04_destaques", "Conteudos"],
    "pauta_aneel": ["05_pauta_aneel", "09_pauta_aneel"],
    "normativos": ["06_normativos_publicados", "10_normativos_publicados"],
    "pendencias": ["07_pendencias", "05_pendencias"],
    "consultas": ["08_consultas", "06_consultas"],
    "leiloes": ["09_leiloes", "07_leiloes"],
    "leiloes_comentarios": ["07_leiloes_comentarios", "09_leiloes_comentarios"],
    "agenda": ["10_agenda", "08_agenda"],
    "opcoes": ["14_listas_controladas", "12_listas_controladas", "Opcoes"],
}


def clean(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_code(value):
    return clean(value).lower()


def is_active(value):
    if pd.isna(value):
        return False
    if value is True:
        return True
    return str(value).strip().lower() in ["true", "1", "sim", "yes", "s"]


def parse_date(value):
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return pd.to_datetime(value, dayfirst=True).to_pydatetime()
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


def format_month(value, lang="pt"):
    date = parse_date(value)
    if date is None:
        return ""
    if lang == "en":
        return f"{MONTHS_EN[date.month]} {date.year}"
    return f"{MONTHS_PT[date.month].capitalize()} {date.year}"


def format_edition_number(value, fallback=None):
    raw = value if not pd.isna(value) else fallback
    if raw is None or pd.isna(raw):
        return ""
    try:
        return f"{int(raw):03d}"
    except Exception:
        return clean(raw)


def build_calendar_days(reference_date):
    first_day = reference_date.replace(day=1)
    blanks = (first_day.weekday() + 1) % 7  # Sunday-first calendar

    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year + 1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1, day=1)

    days_in_month = (next_month - timedelta(days=1)).day
    return [""] * blanks + [str(day) for day in range(1, days_in_month + 1)]


def get_value(row, *possible_columns, default=""):
    for col in possible_columns:
        if col in row.index:
            value = row.get(col)
            if not pd.isna(value):
                return value
    return default


def get_text(row, *possible_columns):
    return clean(get_value(row, *possible_columns))


def get_bool(row, *possible_columns):
    return is_active(get_value(row, *possible_columns))


def find_header_row(raw):
    for i, row in raw.iterrows():
        values = [str(v).strip().lower() for v in row.tolist()]
        if "id" in values:
            return i
    return None


def read_sheet(xls, logical_name, required=True):
    for sheet_name in SHEET_NAMES[logical_name]:
        if sheet_name in xls.sheet_names:
            raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            header_row = find_header_row(raw)
            if header_row is None:
                if required:
                    raise ValueError(f"Cabeçalho com coluna 'id' não encontrado na aba {sheet_name}")
                return pd.DataFrame()

            headers = [clean(h) for h in raw.iloc[header_row].tolist()]
            df = raw.iloc[header_row + 1 :].copy()
            df.columns = headers
            df = df.loc[:, [bool(str(c).strip()) and not str(c).startswith("Unnamed") for c in df.columns]]
            df = df.dropna(how="all")
            return df

    if required:
        raise ValueError(
            f"Aba não encontrada para '{logical_name}'. Tentei: {SHEET_NAMES[logical_name]}"
        )
    return pd.DataFrame()


def active_rows(df):
    if df.empty:
        return df
    if "ativo" not in df.columns:
        return df
    return df[df["ativo"].apply(is_active)]


def filter_by_edition(df, edicao_id):
    if df.empty or "edicao_id" not in df.columns:
        return df
    return df[df["edicao_id"].astype(str).str.strip() == str(edicao_id).strip()]


def sort_by_order(df):
    if df.empty:
        return df
    if "ordem" in df.columns:
        return df.sort_values(by="ordem", na_position="last")
    return df


def build_option_map(opcoes):
    option_map = {}
    if opcoes.empty:
        return option_map

    if {"grupo", "code"}.issubset(set(opcoes.columns)):
        for _, row in opcoes.iterrows():
            grupo = normalize_code(row.get("grupo"))
            code = normalize_code(row.get("code"))
            label_pt = get_text(row, "label_pt", "nome_pt") or code
            label_en = get_text(row, "label_en", "nome_en") or label_pt
            if grupo and code:
                for key in [grupo, grupo.replace("_code", "")]:
                    option_map[(key, code, "pt")] = label_pt
                    option_map[(key, code, "en")] = label_en
        return option_map

    columns = list(opcoes.columns)
    group_indexes = []
    for i, col in enumerate(columns):
        col_norm = normalize_code(col)
        if col_norm.endswith("_code") or col_norm == "idioma_padrao":
            group_indexes.append(i)

    for pos, i in enumerate(group_indexes):
        group_col = columns[i]
        group = normalize_code(group_col)
        next_group_i = group_indexes[pos + 1] if pos + 1 < len(group_indexes) else len(columns)
        label_candidates = columns[i + 1 : next_group_i]

        label_pt_col = next((c for c in label_candidates if normalize_code(c).startswith("label_pt")), None)
        label_en_col = next((c for c in label_candidates if normalize_code(c).startswith("label_en")), None)

        for _, row in opcoes.iterrows():
            code = normalize_code(row.get(group_col))
            if not code:
                continue
            label_pt = clean(row.get(label_pt_col)) if label_pt_col else code
            label_en = clean(row.get(label_en_col)) if label_en_col else label_pt
            label_pt = label_pt or code
            label_en = label_en or label_pt
            for key in [group, group.replace("_code", "")]:
                option_map[(key, code, "pt")] = label_pt
                option_map[(key, code, "en")] = label_en

    return option_map


def label(option_map, grupo, code, lang="pt"):
    code = normalize_code(code)
    if not code:
        return ""
    return option_map.get((grupo, code, lang), option_map.get((grupo + "_code", code, lang), code))


def bilingual_item(
    row,
    title_pt="",
    title_en="",
    detail_pt="",
    detail_en="",
    summary_pt="",
    summary_en="",
):
    title_pt = clean(title_pt)
    title_en = clean(title_en) or title_pt
    detail_pt = clean(detail_pt)
    detail_en = clean(detail_en) or detail_pt
    summary_pt = clean(summary_pt)
    summary_en = clean(summary_en) or summary_pt

    return {
        "title": title_pt,
        "title_pt": title_pt,
        "title_en": title_en,
        "summary": summary_pt,
        "summary_pt": summary_pt,
        "summary_en": summary_en,
        "detail": detail_pt,
        "detail_pt": detail_pt,
        "detail_en": detail_en,
        "agency": get_text(row, "orgao_sigla"),
        "status": "",
        "status_pt": "",
        "status_en": "",
        "level": get_text(row, "criticidade_code"),
        "level_pt": get_text(row, "criticidade_pt", "criticidade_code"),
        "level_en": get_text(row, "criticidade_en", "criticidade_code"),
        "change": get_text(row, "mudanca_code"),
        "change_pt": get_text(row, "mudanca_pt", "mudanca_code"),
        "change_en": get_text(row, "mudanca_en", "mudanca_code"),
        "deadline": "",
        "date": "",
        "datePrecision": "",
        "type": "",
        "type_pt": "",
        "type_en": "",
        "referenceNumber": get_text(row, "numero_referencia", "numero"),
        "number": get_text(row, "numero_referencia", "numero"),
        "link": get_text(row, "link_referencia"),
        "tags": get_text(row, "tags"),
    }


def set_bilingual_label(item, field, pt, en=None):
    pt = clean(pt)
    en = clean(en) or pt
    item[field] = pt
    item[f"{field}_pt"] = pt
    item[f"{field}_en"] = en


def build_highlights(df):
    items = []
    for _, row in sort_by_order(active_rows(df)).iterrows():
        title_pt = get_text(row, "titulo_pt")
        if not title_pt:
            continue
        item = bilingual_item(
            row,
            title_pt=title_pt,
            title_en=get_text(row, "titulo_en"),
            detail_pt=get_text(row, "comentario_pt", "detalhe_pt"),
            detail_en=get_text(row, "comentario_en", "detalhe_en"),
            summary_pt=get_text(row, "resumo_pt"),
            summary_en=get_text(row, "resumo_en"),
        )
        set_bilingual_label(item, "status", get_text(row, "status", "status_code"))
        set_bilingual_label(item, "type", get_text(row, "tipo_destaque_code", "subtipo_code"))
        items.append(item)
    return items


def build_pauta_aneel(df, option_map):
    items = []
    for _, row in sort_by_order(active_rows(df)).iterrows():
        item_title_pt = get_text(row, "item_pt", "titulo_pt", "assunto_pt")
        item_title_en = get_text(row, "item_en", "titulo_en", "assunto_en")
        meeting_title_pt = get_text(row, "titulo_reuniao_pt")
        meeting_title_en = get_text(row, "titulo_reuniao_en")
        title_pt = item_title_pt or meeting_title_pt
        title_en = item_title_en or meeting_title_en or title_pt
        if not title_pt:
            continue
        tipo_code = get_text(row, "tipo_reuniao_code", "tipo_evento_code", "subtipo_code")
        item = bilingual_item(
            row,
            title_pt=title_pt,
            title_en=title_en,
            detail_pt=get_text(row, "comentario_pt", "detalhe_pt"),
            detail_en=get_text(row, "comentario_en", "detalhe_en"),
            summary_pt=meeting_title_pt,
            summary_en=meeting_title_en,
        )
        item["agency"] = get_text(row, "orgao_sigla") or "ANEEL"
        item["date"] = format_date(get_value(row, "data_reuniao", "data_evento"))
        set_bilingual_label(
            item,
            "type",
            label(option_map, "tipo_reuniao_aneel", tipo_code, "pt") or label(option_map, "tipo_evento", tipo_code, "pt"),
            label(option_map, "tipo_reuniao_aneel", tipo_code, "en") or label(option_map, "tipo_evento", tipo_code, "en"),
        )
        items.append(item)
    return items


def build_normativos(df, option_map):
    items = []
    for _, row in sort_by_order(active_rows(df)).iterrows():
        title_pt = get_text(row, "titulo_pt", "normativo_pt")
        if not title_pt:
            continue
        status_code = get_text(row, "status_normativo_code", "status_code")
        tipo_code = get_text(row, "tipo_normativo_code", "subtipo_code")
        item = bilingual_item(
            row,
            title_pt=title_pt,
            title_en=get_text(row, "titulo_en", "normativo_en"),
            detail_pt=get_text(row, "resumo_pt", "comentario_pt", "detalhe_pt"),
            detail_en=get_text(row, "resumo_en", "comentario_en", "detalhe_en"),
            summary_pt=get_text(row, "resumo_pt"),
            summary_en=get_text(row, "resumo_en"),
        )
        set_bilingual_label(item, "status", label(option_map, "status_normativo", status_code, "pt"), label(option_map, "status_normativo", status_code, "en"))
        item["date"] = format_date(get_value(row, "data_publicacao", "data_evento"))
        set_bilingual_label(item, "type", label(option_map, "tipo_normativo", tipo_code, "pt") or tipo_code, label(option_map, "tipo_normativo", tipo_code, "en") or tipo_code)
        items.append(item)
    return items


def build_pendencias(df, option_map):
    items = []
    for _, row in sort_by_order(active_rows(df)).iterrows():
        title_pt = get_text(row, "topico_pt", "titulo_pt")
        if not title_pt:
            continue
        status_code = get_text(row, "status_regulatorio_code", "status_code")
        item = bilingual_item(
            row,
            title_pt=title_pt,
            title_en=get_text(row, "topico_en", "titulo_en"),
            detail_pt=get_text(row, "comentario_pt", "detalhe_pt"),
            detail_en=get_text(row, "comentario_en", "detalhe_en"),
        )
        set_bilingual_label(item, "status", label(option_map, "status_regulatorio", status_code, "pt"), label(option_map, "status_regulatorio", status_code, "en"))
        set_bilingual_label(item, "type", "Pendência regulatória", "Regulatory topic")
        items.append(item)
    return items


def build_consultas(df, option_map):
    items = []
    for _, row in sort_by_order(active_rows(df)).iterrows():
        title_pt = get_text(row, "titulo_pt", "topico_pt")
        if not title_pt:
            continue
        tipo_code = get_text(row, "tipo_consulta_code", "subtipo_code")
        status_code = get_text(row, "status_consulta_code", "status_code")
        numero = get_text(row, "numero", "numero_referencia")
        item = bilingual_item(
            row,
            title_pt=title_pt,
            title_en=get_text(row, "titulo_en", "topico_en"),
            detail_pt=get_text(row, "comentario_pt", "detalhe_pt"),
            detail_en=get_text(row, "comentario_en", "detalhe_en"),
        )
        set_bilingual_label(item, "status", label(option_map, "status_consulta", status_code, "pt"), label(option_map, "status_consulta", status_code, "en"))
        item["deadline"] = format_date(get_value(row, "prazo", "prazo_data"))
        set_bilingual_label(item, "type", label(option_map, "tipo_consulta", tipo_code, "pt"), label(option_map, "tipo_consulta", tipo_code, "en"))
        item["referenceNumber"] = numero
        item["number"] = numero
        items.append(item)
    return items


def build_leiloes(df, option_map, comentarios_df=None, edicao_id=None):
    items = []
    for _, row in sort_by_order(active_rows(df)).iterrows():
        title_pt = get_text(row, "titulo_pt", "tipo_leilao_pt")
        if not title_pt:
            continue
        status_code = get_text(row, "status_leilao_code", "status_code")
        detail_pt = get_text(row, "comentario_pt", "detalhe_pt")
        detail_en = get_text(row, "comentario_en", "detalhe_en")
        step_pt = get_text(row, "proximo_passo_pt")
        step_en = get_text(row, "proximo_passo_en")
        if step_pt:
            detail_pt = f"{detail_pt}\n\nPróximo passo: {step_pt}" if detail_pt else f"Próximo passo: {step_pt}"
        if step_en:
            detail_en = f"{detail_en}\n\nNext step: {step_en}" if detail_en else f"Next step: {step_en}"
        item = bilingual_item(
            row,
            title_pt=title_pt,
            title_en=get_text(row, "titulo_en", "tipo_leilao_en"),
            detail_pt=detail_pt,
            detail_en=detail_en,
            summary_pt=step_pt,
            summary_en=step_en,
        )
        set_bilingual_label(item, "status", label(option_map, "status_leilao", status_code, "pt"), label(option_map, "status_leilao", status_code, "en"))
        item["date"] = get_text(row, "data_estimada_pt") or format_date(get_value(row, "data_estimada"))
        item["date_pt"] = get_text(row, "data_estimada_pt") or item["date"]
        item["date_en"] = get_text(row, "data_estimada_en") or item["date"]
        set_bilingual_label(item, "type", "Leilão", "Auction")
        items.append(item)

    if comentarios_df is not None and not comentarios_df.empty and edicao_id is not None:
        comments = filter_by_edition(active_rows(comentarios_df), edicao_id)
        for _, row in comments.iterrows():
            comment_pt = get_text(row, "comentario_geral_pt")
            if comment_pt:
                item = bilingual_item(
                    row,
                    title_pt="Comentários gerais sobre os próximos leilões",
                    title_en="General comments on upcoming auctions",
                    detail_pt=comment_pt,
                    detail_en=get_text(row, "comentario_geral_en") or comment_pt,
                )
                item["agency"] = "MME/ANEEL"
                set_bilingual_label(item, "type", "Comentário", "Comment")
                item["tags"] = "leiloes"
                items.append(item)
    return items


def split_dates(value):
    text = clean(value)
    if not text:
        return []
    parts = [p.strip() for p in text.replace(",", ";").split(";") if p.strip()]
    dates = []
    for part in parts:
        parsed = parse_date(part)
        if parsed is not None:
            dates.append(parsed)
    return dates


def month_bounds(reference_date):
    first = reference_date.replace(day=1)
    if first.month == 12:
        next_month = first.replace(year=first.year + 1, month=1, day=1)
    else:
        next_month = first.replace(month=first.month + 1, day=1)
    return first, next_month - timedelta(days=1)


def recurrence_dates(row, reference_date):
    dates = []
    for col in ["datas_exibicao", "datas_calendario"]:
        if col in row.index:
            dates.extend(split_dates(row.get(col)))

    event_date = parse_date(get_value(row, "data_evento"))
    if event_date is not None:
        dates.append(event_date)

    tipo_agenda_code = normalize_code(get_value(row, "tipo_agenda_code"))
    if tipo_agenda_code != "recurring" and not get_bool(row, "recorrente"):
        # Some rows use data_inicio/data_fim as exact dates for calendar-specific events.
        for col in ["data_inicio", "data_fim"]:
            d = parse_date(get_value(row, col))
            if d is not None and d == parse_date(get_value(row, "data_inicio")):
                dates.append(d)
        return sorted(set(dates))

    freq = normalize_code(get_value(row, "frequencia_code"))
    weekday_code = normalize_code(get_value(row, "dia_semana_code"))
    weekday = WEEKDAY_TO_NUMBER.get(weekday_code)
    if weekday is None:
        for col in ["data_inicio", "data_fim"]:
            d = parse_date(get_value(row, col))
            if d is not None:
                dates.append(d)
        return sorted(set(dates))

    first_month_day, last_month_day = month_bounds(reference_date)
    start = parse_date(get_value(row, "data_inicio")) or first_month_day
    end = parse_date(get_value(row, "data_fim")) or last_month_day
    start = max(start, first_month_day)
    end = min(end, last_month_day)
    if start > end:
        return sorted(set(dates))

    current = start
    while current.weekday() != weekday:
        current += timedelta(days=1)

    all_occurrences = []
    while current <= end:
        all_occurrences.append(current)
        current += timedelta(days=7)

    order = normalize_code(get_value(row, "ordem_dia_semana"))
    if freq == "weekly" or order in ["", "all"]:
        dates.extend(all_occurrences)
    elif freq == "biweekly":
        dates.extend(all_occurrences[::2])
    elif freq == "monthly":
        order_map = {"first": 0, "second": 1, "third": 2, "fourth": 3}
        if order == "last" and all_occurrences:
            dates.append(all_occurrences[-1])
        elif order in order_map and len(all_occurrences) > order_map[order]:
            dates.append(all_occurrences[order_map[order]])
    return sorted(set(dates))


def build_agenda(df, data_edicao, option_map):
    agenda = {
        "month": format_month(data_edicao, "pt"),
        "month_pt": format_month(data_edicao, "pt"),
        "month_en": format_month(data_edicao, "en"),
        "days": build_calendar_days(data_edicao),
        "eventDays": [],
        "events": [],
    }

    for _, row in sort_by_order(active_rows(df)).iterrows():
        title_pt = get_text(row, "titulo_pt")
        if not title_pt:
            continue

        tipo_evento_code = get_text(row, "tipo_evento_code", "subtipo_code")
        dates = recurrence_dates(row, data_edicao)
        display_dates = [d.strftime("%d/%m/%Y") for d in dates]

        for d in dates:
            if d.month == data_edicao.month and d.year == data_edicao.year:
                day = str(d.day)
                if day not in agenda["eventDays"]:
                    agenda["eventDays"].append(day)

        event_date = parse_date(get_value(row, "data_evento"))
        desc_pt = get_text(row, "descricao_recorrencia_pt", "descricao")
        desc_en = get_text(row, "descricao_recorrencia_en") or desc_pt
        event = {
            "title": title_pt,
            "title_pt": title_pt,
            "title_en": get_text(row, "titulo_en") or title_pt,
            "date": format_date(event_date) if event_date else "",
            "agency": get_text(row, "orgao_sigla"),
            "type": label(option_map, "tipo_evento", tipo_evento_code, "pt"),
            "type_pt": label(option_map, "tipo_evento", tipo_evento_code, "pt"),
            "type_en": label(option_map, "tipo_evento", tipo_evento_code, "en"),
            "link": get_text(row, "link_referencia"),
            "agendaType": get_text(row, "tipo_agenda_code"),
            "recurring": get_bool(row, "recorrente"),
            "frequency": get_text(row, "frequencia_code"),
            "weekday": get_text(row, "dia_semana_code"),
            "weekdayOrder": get_text(row, "ordem_dia_semana"),
            "startDate": format_date(get_value(row, "data_inicio")),
            "endDate": format_date(get_value(row, "data_fim")),
            "recurrenceDescription": desc_pt,
            "recurrenceDescription_pt": desc_pt,
            "recurrenceDescription_en": desc_en,
            "displayDates": display_dates,
        }
        agenda["events"].append(event)

    agenda["eventDays"] = sorted(agenda["eventDays"], key=lambda x: int(x))
    return agenda


def build_available_editions(edicoes):
    items = []
    edicoes = active_rows(edicoes)
    if "data_edicao" in edicoes.columns:
        edicoes = edicoes.sort_values(by="data_edicao", ascending=False)

    for index, row in edicoes.iterrows():
        data_edicao = parse_date(row.get("data_edicao"))
        if data_edicao is None:
            continue
        edition_date = data_edicao.strftime("%Y-%m-%d")
        edition_number = format_edition_number(get_value(row, "numero_edicao", default=index + 1))
        edicao_id = get_text(row, "id") or f"ed_{edition_date}"
        label_pt = f"Edição #{edition_number}" if edition_number else get_text(row, "titulo_pt")
        label_en = f"Edition #{edition_number}" if edition_number else get_text(row, "titulo_en") or label_pt
        items.append(
            {
                "id": edicao_id,
                "edition": edition_date,
                "editionNumber": edition_number,
                "label": label_pt,
                "label_pt": label_pt,
                "label_en": label_en,
                "title_pt": get_text(row, "titulo_pt"),
                "title_en": get_text(row, "titulo_en") or get_text(row, "titulo_pt"),
                "summary_pt": get_text(row, "resumo_pt"),
                "summary_en": get_text(row, "resumo_en") or get_text(row, "resumo_pt"),
                "month_pt": format_month(data_edicao, "pt"),
                "month_en": format_month(data_edicao, "en"),
                "status": get_text(row, "status_edicao_code", "status_code"),
            }
        )
    return items


def build_result_for_edition(edicao, edicao_index, dfs, option_map):
    data_edicao = parse_date(edicao["data_edicao"])
    if data_edicao is None:
        raise ValueError("Data da edição não encontrada na aba 01_edicoes")

    edicao_id = get_text(edicao, "id")
    edition_date = data_edicao.strftime("%Y-%m-%d")
    edition_number = format_edition_number(
        get_value(edicao, "numero_edicao", default=edicao_index + 1)
    )

    period_start = format_date(get_value(edicao, "periodo_inicio"))
    period_end = format_date(get_value(edicao, "periodo_fim"))
    period = f"{period_start} a {period_end}" if period_start and period_end else format_month(data_edicao, "pt")
    period_en = f"{period_start} to {period_end}" if period_start and period_end else format_month(data_edicao, "en")
    updated_at = format_datetime(get_value(edicao, "updated_at", "publicada_em"))

    pendencias = filter_by_edition(dfs["pendencias"], edicao_id)
    if not pendencias.empty and "orgao_sigla" in pendencias.columns:
        orgaos = pendencias["orgao_sigla"].astype(str).str.strip().str.upper()
        aneel_topics = pendencias[orgaos == "ANEEL"]
        mme_topics = pendencias[orgaos == "MME"]
    else:
        aneel_topics = pd.DataFrame()
        mme_topics = pd.DataFrame()

    agenda_df = filter_by_edition(dfs["agenda"], edicao_id)
    if agenda_df.empty and not dfs["agenda"].empty:
        # For the MVP, the institutional calendar can be maintained once per month.
        # If an edition has no agenda rows, reuse the general agenda rows available in the workbook.
        agenda_df = dfs["agenda"]

    result = {
        "edition": edition_date,
        "editionNumber": edition_number,
        "editionId": edicao_id or f"cpfl-{edition_number}",
        "client": "CPFL Energia",
        "title": get_text(edicao, "titulo_pt"),
        "title_pt": get_text(edicao, "titulo_pt"),
        "title_en": get_text(edicao, "titulo_en") or get_text(edicao, "titulo_pt"),
        "summary": get_text(edicao, "resumo_pt"),
        "summary_pt": get_text(edicao, "resumo_pt"),
        "summary_en": get_text(edicao, "resumo_en") or get_text(edicao, "resumo_pt"),
        "month": format_month(data_edicao, "pt"),
        "month_pt": format_month(data_edicao, "pt"),
        "month_en": format_month(data_edicao, "en"),
        "periodStart": period_start,
        "periodEnd": period_end,
        "period": period,
        "period_pt": period,
        "period_en": period_en,
        "updatedAt": updated_at,
        "highlights": build_highlights(filter_by_edition(dfs["destaques"], edicao_id)),
        "aneelAgenda": build_pauta_aneel(filter_by_edition(dfs["pauta_aneel"], edicao_id), option_map),
        "publishedRules": build_normativos(filter_by_edition(dfs["normativos"], edicao_id), option_map),
        "aneelTopics": build_pendencias(aneel_topics, option_map),
        "mmeTopics": build_pendencias(mme_topics, option_map),
        "publicParticipation": build_consultas(filter_by_edition(dfs["consultas"], edicao_id), option_map),
        "auctions": build_leiloes(
            filter_by_edition(dfs["leiloes"], edicao_id),
            option_map,
            comentarios_df=dfs.get("leiloes_comentarios"),
            edicao_id=edicao_id,
        ),
        "agenda": build_agenda(agenda_df, data_edicao, option_map),
    }
    return result


def js_string(value):
    return json.dumps(value, ensure_ascii=False)


def write_editions_js(available_editions, output_dir):
    lines = []
    for item in available_editions:
        var_name = "edition" + item["edition"].replace("-", "")
        lines.append(f'import {var_name} from "./edition-{item["edition"]}.json";')

    lines.append("\nconst editions = [")
    for item in available_editions:
        var_name = "edition" + item["edition"].replace("-", "")
        lines.append("  {")
        lines.append(f'    id: {js_string(item["id"])},')
        lines.append(f'    label: {js_string(item["label_pt"])},')
        lines.append(f'    label_pt: {js_string(item["label_pt"])},')
        lines.append(f'    label_en: {js_string(item["label_en"])},')
        lines.append(f'    date: {js_string(item["edition"])},')
        lines.append(f"    data: {var_name},")
        lines.append("  },")
    lines.append("];\n")
    lines.append("export default editions;\n")

    (output_dir / "editions.js").write_text("\n".join(lines), encoding="utf-8")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    xls = pd.ExcelFile(INPUT_FILE)
    edicoes = read_sheet(xls, "edicoes")
    opcoes = read_sheet(xls, "opcoes", required=False)

    dfs = {
        "destaques": read_sheet(xls, "destaques", required=False),
        "pauta_aneel": read_sheet(xls, "pauta_aneel", required=False),
        "normativos": read_sheet(xls, "normativos", required=False),
        "pendencias": read_sheet(xls, "pendencias", required=False),
        "consultas": read_sheet(xls, "consultas", required=False),
        "leiloes": read_sheet(xls, "leiloes", required=False),
        "leiloes_comentarios": read_sheet(xls, "leiloes_comentarios", required=False),
        "agenda": read_sheet(xls, "agenda", required=False),
    }

    option_map = build_option_map(opcoes)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for old_file in OUTPUT_DIR.glob("edition-*.json"):
        old_file.unlink()

    edicoes_ativas = active_rows(edicoes)
    if "data_edicao" in edicoes_ativas.columns:
        edicoes_ativas = edicoes_ativas.sort_values(by="data_edicao", ascending=False)

    available_editions = []
    for index, edicao in edicoes_ativas.iterrows():
        status = get_text(edicao, "status_edicao_code", "status_code")
        if status and normalize_code(status) not in ["published", "publicada"]:
            continue

        data_edicao = parse_date(edicao.get("data_edicao"))
        if data_edicao is None:
            print(f"Edição ignorada por falta de data: linha {index + 2}")
            continue

        result = build_result_for_edition(edicao, index, dfs, option_map)
        edition_date = data_edicao.strftime("%Y-%m-%d")
        output_file = OUTPUT_DIR / f"edition-{edition_date}.json"
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"JSON criado com sucesso: {output_file}")

        available_editions.append(
            {
                "id": result["editionId"],
                "edition": result["edition"],
                "editionNumber": result["editionNumber"],
                "label_pt": f"Edição #{result['editionNumber']}",
                "label_en": f"Edition #{result['editionNumber']}",
            }
        )

    available_editions = sorted(available_editions, key=lambda x: x["edition"], reverse=True)

    with (OUTPUT_DIR / "editions.json").open("w", encoding="utf-8") as f:
        json.dump(available_editions, f, ensure_ascii=False, indent=2)

    write_editions_js(available_editions, OUTPUT_DIR)
    print(f"Índice criado com sucesso: {OUTPUT_DIR / 'editions.js'}")


if __name__ == "__main__":
    main()
