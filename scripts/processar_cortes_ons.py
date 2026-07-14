#!/usr/bin/env python3
"""
processar_cortes_ons.py
-----------------------
Processa dados de C-OFF fotovoltaico (UFV) e eólico (EOL) do ONS
e gera um dashboard HTML interativo.

COMO USAR:
  1. Mantenha este script na mesma pasta dos arquivos .parquet baixados do ONS
     (o script sempre usa a pasta onde ele mesmo está salvo, não importa onde
     essa pasta viva — inclusive dentro de uma pasta sincronizada de nuvem
     como Google Drive, OneDrive ou SharePoint).
  2. Abra o Terminal e navegue até essa pasta, por exemplo:
       cd "/caminho/da/sua/pasta/Cortes - teste"
  3. Execute:
       python3 processar_cortes_ons.py              # lê arquivos locais + baixa meses novos
       python3 processar_cortes_ons.py --so-local   # só arquivos já baixados, sem internet
       python3 processar_cortes_ons.py --mes 2026-05
       python3 processar_cortes_ons.py --inicio 2025-01 --fim 2026-06
       python3 processar_cortes_ons.py --fonte EOL  # só eólica

DEPENDÊNCIAS:
  pip install pandas fastparquet boto3

ATUALIZAÇÃO INCREMENTAL:
  Os arquivos são lidos diretamente do bucket público do ONS na AWS
  (leitura anônima via boto3, sem necessidade de baixar manualmente).
  Um arquivo _manifest_ons.csv guarda ETag/LastModified/tamanho de cada
  mês já processado, então cada execução só baixa de novo o que for novo
  ou tiver sido alterado retroativamente pelo ONS.

LOGO:
  Coloque um arquivo chamado "logo.png" (ou logo.svg) na mesma pasta.
  O script embute a logo automaticamente no dashboard.

SAÍDA:
  dashboard_cortes.html  — abrir no navegador. Esse arquivo já contém todos
  os dados embutidos (não depende de internet nem do script pra ser aberto),
  então pra compartilhar o dashboard com outras pessoas basta compartilhar
  só esse arquivo — não é necessário dar acesso à pasta inteira do projeto
  (que tem o script, o cache de parquets e os arquivos de controle interno).

  Só rode este script em UMA máquina por vez sobre a mesma pasta. Se essa
  pasta estiver sincronizada numa nuvem (Google Drive/OneDrive/SharePoint) e
  mais de uma pessoa rodar o script ao mesmo tempo, os arquivos de controle
  (_manifest_ons.csv, cadastro_ponto_conexao.csv, cache_ons/) podem entrar em
  conflito de sincronização e corromper o controle incremental.
"""

import argparse
import base64
import calendar
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, date, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd

try:
    import boto3
    from botocore import UNSIGNED
    from botocore.client import Config
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

# ─── S3 do ONS (bucket público, leitura anônima) ─────────────────────────────
BUCKET_ONS = "ons-aws-prod-opendata"

S3_PREFIXES = {
    "UFV": {
        "conj":   "dataset/restricao_coff_fotovoltaica_tm/",
        "detail": "dataset/restricao_coff_fotovoltaica_detail_tm/",
    },
    "EOL": {
        "conj":   "dataset/restricao_coff_eolica_tm/",
        "detail": "dataset/restricao_coff_eolica_detail_tm/",
    },
}

MANIFEST_COLS = ["fonte", "tipo", "ano", "mes", "etag", "last_modified_utc", "size"]

_s3_client = None


def get_s3_client():
    """Cliente S3 único, com acesso anônimo (o bucket do ONS é público)."""
    global _s3_client
    if boto3 is None:
        raise RuntimeError("boto3 não instalado. Rode: pip install boto3")
    if _s3_client is None:
        _s3_client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    return _s3_client


# ─── Ponto de conexão (cadastro auxiliar, dataset "Fator de Capacidade") ─────
# O arquivo de corte (restricao_coff_*) não tem a subestação/ponto de conexão —
# só o conjunto de usinas. Essa informação vive num dataset cadastral separado
# do ONS ("Fator de Capacidade"), ligado ao nosso dado pela coluna id_ons.
FATOR_CAPACIDADE_PREFIX = "dataset/fator_capacidade_2_di/"
CADASTRO_PONTO_CONEXAO_CSV = "cadastro_ponto_conexao.csv"
CADASTRO_PONTO_CONEXAO_COLS = ["fonte", "id_ons", "nom_pontoconexao", "atualizado_em_utc"]


def _norm_tipo_usina(v) -> str:
    s = "" if v is None else str(v).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def _fonte_por_tipo_usina(v):
    k = _norm_tipo_usina(v)
    if k in ("EOLICA", "EOLIELETRICA"):
        return "EOL"
    if k in ("SOLAR", "FOTOVOLTAICA"):
        return "UFV"
    return None


def carregar_cadastro_ponto_conexao(path: Path) -> dict:
    if not path.exists():
        return {}
    df = pd.read_csv(path, sep=";", dtype=str, low_memory=False)
    cadastro = {}
    for _, row in df.iterrows():
        fonte = str(row.get("fonte", "")).strip()
        id_ons = str(row.get("id_ons", "")).strip()
        ponto = row.get("nom_pontoconexao", "")
        if fonte and id_ons:
            cadastro[(fonte, id_ons)] = ponto
    return cadastro


def salvar_cadastro_ponto_conexao(cadastro: dict, path: Path) -> None:
    agora = datetime.now(timezone.utc).isoformat()
    linhas = [
        {"fonte": f, "id_ons": i, "nom_pontoconexao": n, "atualizado_em_utc": agora}
        for (f, i), n in cadastro.items()
    ]
    df = pd.DataFrame(linhas, columns=CADASTRO_PONTO_CONEXAO_COLS)
    if not df.empty:
        df = df.sort_values(["fonte", "id_ons"], kind="mergesort")
    df.to_csv(path, sep=";", index=False, encoding="utf-8")


def _fator_capacidade_key_candidatos(ano: int, mes: int):
    """
    Candidatos de nome de arquivo para o Fator de Capacidade no S3. O ONS já usou
    pequenas variações de separador nesse dataset, então tentamos as mais prováveis
    em ordem, e seguimos em frente se nenhuma existir para aquele mês.
    """
    return [
        f"{FATOR_CAPACIDADE_PREFIX}FATOR_CAPACIDADE-2_{ano}_{mes:02d}.parquet",
        f"{FATOR_CAPACIDADE_PREFIX}FATOR_CAPACIDADE_2_{ano}_{mes:02d}.parquet",
        f"{FATOR_CAPACIDADE_PREFIX}FATOR_CAPACIDADE-2_{ano}_{mes:02d}.csv",
    ]


def buscar_fator_capacidade(ano: int, mes: int):
    """Baixa o Fator de Capacidade do ONS para ano/mes. Retorna (DataFrame, chave_s3) ou (None, None)."""
    for key in _fator_capacidade_key_candidatos(ano, mes):
        try:
            resp = get_s3_client().get_object(Bucket=BUCKET_ONS, Key=key)
        except ClientError as e:
            codigo = e.response.get("Error", {}).get("Code", "")
            if codigo in ("404", "NoSuchKey", "NotFound"):
                continue
            raise

        raw = resp["Body"].read()
        try:
            if key.lower().endswith(".csv"):
                df = pd.read_csv(BytesIO(raw), sep=None, engine="python", dtype=str)
            else:
                df = pd.read_parquet(BytesIO(raw))
            return df, key
        except Exception as e:
            print(f"  [aviso] falha ao ler Fator de Capacidade ({key}): {e}")
            return None, None

    return None, None


def atualizar_cadastro_ponto_conexao(cadastro: dict, fonte: str, ano: int, mes: int, ids_necessarios) -> None:
    """
    Preenche, no cadastro em memória, o ponto de conexão dos id_ons que ainda não
    têm registro. Só busca o Fator de Capacidade se houver algum id_ons faltando.
    """
    faltantes = {str(i).strip() for i in ids_necessarios if (fonte, str(i).strip()) not in cadastro}
    faltantes.discard("")
    if not faltantes:
        return

    df_fc, origem = buscar_fator_capacidade(ano, mes)
    if df_fc is None or df_fc.empty:
        print(f"  [aviso] Fator de Capacidade não encontrado para {ano}-{mes:02d} — "
              f"ponto de conexão fica em branco para {len(faltantes)} id(s) neste mês")
        return

    cols_lower = {c.lower(): c for c in df_fc.columns}
    col_id    = cols_lower.get("id_ons")
    col_tipo  = cols_lower.get("nom_tipousina")
    col_ponto = cols_lower.get("nom_pontoconexao")

    if not (col_id and col_tipo and col_ponto):
        print(f"  [aviso] Fator de Capacidade ({origem}) não tem as colunas esperadas "
              f"(id_ons/nom_tipousina/nom_pontoconexao) — colunas disponíveis: {list(df_fc.columns)[:20]}")
        return

    d = df_fc[[col_id, col_tipo, col_ponto]].copy()
    d.columns = ["id_ons", "nom_tipousina", "nom_pontoconexao"]
    d["id_ons"] = d["id_ons"].astype(str).str.strip()
    d["fonte"]  = d["nom_tipousina"].map(_fonte_por_tipo_usina)
    d = d[d["fonte"] == fonte]
    d["nom_pontoconexao"] = d["nom_pontoconexao"].astype(str).str.strip()
    d = d[d["nom_pontoconexao"] != ""]
    d = d.drop_duplicates(subset=["id_ons"], keep="last")

    encontrados = 0
    for _, row in d.iterrows():
        if row["id_ons"] in faltantes:
            cadastro[(fonte, row["id_ons"])] = row["nom_pontoconexao"]
            encontrados += 1

    print(f"  [cadastro ponto de conexão] {encontrados}/{len(faltantes)} id(s) "
          f"encontrados via Fator de Capacidade {ano}-{mes:02d} ({origem})")

# Nomes locais dos arquivos (padrão ONS)
NOMES_LOCAIS = {
    "UFV": {
        "conj":   "RESTRICAO_COFF_FOTOVOLTAICA_{ano}_{mes:02d}.parquet",
        "detail": "RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_{ano}_{mes:02d}.parquet",
    },
    "EOL": {
        "conj":   "RESTRICAO_COFF_EOLICA_{ano}_{mes:02d}.parquet",
        "detail": "RESTRICAO_COFF_EOLICA_DETAIL_{ano}_{mes:02d}.parquet",
    },
}

MES_INICIAL = date(2024, 4, 1)

DIR_CACHE  = Path("cache_ons")
DIR_LOCAL  = Path(".")   # pasta onde o script está / onde estão os parquets
DIR_CACHE.mkdir(exist_ok=True)

# Subpastas locais onde o script procura os parquets, por fonte
# Pode criar "Cortes UFV/" para organizar os arquivos UFV também
SUBDIRS_FONTE = {
    "UFV": [".", "Cortes UFV", "UFV", "Solar"],
    "EOL": [".", "Cortes Eólicas", "Cortes Eolicas", "EOL", "Eolica"],
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def meses_entre(inicio: date, fim: date):
    cur = date(inicio.year, inicio.month, 1)
    fim = date(fim.year,   fim.month,   1)
    while cur <= fim:
        yield cur.year, cur.month
        cur = date(cur.year + (cur.month // 12), cur.month % 12 + 1, 1)


def horas_mes(ano: int, mes: int) -> int:
    return calendar.monthrange(ano, mes)[1] * 24


# ─── Manifest de controle incremental (ETag/LastModified/tamanho) ───────────

def carregar_manifest(path: Path) -> dict:
    """
    Carrega o manifest em um dict {(fonte,tipo,ano,mes): {etag,last_modified_utc,size}}.
    Guarda, por arquivo mensal, os metadados do S3 na última execução em que foi baixado.
    """
    if not path.exists():
        return {}

    df = pd.read_csv(path, sep=";", dtype=str, low_memory=False)
    for c in MANIFEST_COLS:
        if c not in df.columns:
            df[c] = ""

    manifest = {}
    for _, row in df.iterrows():
        chave = (row["fonte"], row["tipo"], str(row["ano"]), str(row["mes"]).zfill(2))
        manifest[chave] = {
            "etag": row["etag"],
            "last_modified_utc": row["last_modified_utc"],
            "size": str(row["size"]),
        }
    return manifest


def salvar_manifest(manifest: dict, path: Path) -> None:
    linhas = []
    for (fonte, tipo, ano, mes), meta in manifest.items():
        linhas.append({"fonte": fonte, "tipo": tipo, "ano": ano, "mes": mes, **meta})

    df = pd.DataFrame(linhas, columns=MANIFEST_COLS)
    if not df.empty:
        df = df.sort_values(["fonte", "tipo", "ano", "mes"], kind="mergesort")
    df.to_csv(path, sep=";", index=False, encoding="utf-8")


def _s3_key(ano: int, mes: int, fonte: str, tipo: str) -> str:
    nome = NOMES_LOCAIS[fonte][tipo].format(ano=ano, mes=mes)
    return S3_PREFIXES[fonte][tipo] + nome


def _head_s3(fonte: str, tipo: str, ano: int, mes: int):
    """
    Consulta só os metadados do arquivo no S3 (sem baixar o conteúdo).
    Retorna None se o arquivo ainda não existir no bucket do ONS (mês futuro/não publicado).
    """
    key = _s3_key(ano, mes, fonte, tipo)
    try:
        resp = get_s3_client().head_object(Bucket=BUCKET_ONS, Key=key)
    except ClientError as e:
        codigo = e.response.get("Error", {}).get("Code", "")
        if codigo in ("404", "NoSuchKey", "NotFound"):
            return None
        raise

    return {
        "key": key,
        "last_modified_utc": resp["LastModified"].astimezone(timezone.utc).isoformat(),
        "etag": str(resp.get("ETag", "")).strip('"'),
        "size": str(int(resp.get("ContentLength", 0))),
    }


def obter_arquivo(ano: int, mes: int, fonte: str, tipo: str, so_local: bool, manifest: dict) -> Path | None:
    """
    Retorna path do parquet, com controle incremental via S3:
    1. Verifica se já existe cópia em cache_ons/ ou numa pasta local da fonte.
    2. Se --so-local, usa só o que já existe (sem tocar na rede).
    3. Caso contrário, consulta os metadados do arquivo no S3 (ETag/LastModified/tamanho):
       - arquivo novo (sem cópia local) -> baixa direto do S3 (bucket público, sem urllib)
       - cópia local já existe e não há registro no manifest -> adota a cópia como
         referência, sem baixar de novo, só grava os metadados atuais
       - manifest indica que o ONS alterou o arquivo (ETag/LastModified/tamanho mudou)
         -> baixa de novo e atualiza o cache
       - nada mudou -> reaproveita o que já está em disco
    """
    nome_local  = NOMES_LOCAIS[fonte][tipo].format(ano=ano, mes=mes)
    nome_cache  = f"{tipo.upper()}_{fonte}_{ano}-{mes:02d}.parquet"
    path_cache  = DIR_CACHE / nome_cache

    path_local = None
    for subdir in SUBDIRS_FONTE.get(fonte, ["."]):
        p = DIR_LOCAL / subdir / nome_local
        if p.exists():
            path_local = p
            break

    # cache tem prioridade sobre a pasta local, pois é onde o script grava atualizações
    path_existente = path_cache if path_cache.exists() else path_local

    if so_local:
        if path_existente:
            print(f"  [local] {path_existente}")
        else:
            print(f"  [aviso] não encontrado localmente: {nome_local}")
        return path_existente

    chave = (fonte, tipo, str(ano), f"{mes:02d}")

    try:
        meta_s3 = _head_s3(fonte, tipo, ano, mes)
    except Exception as e:
        print(f"  [aviso] falha ao consultar o S3 do ONS ({e})")
        if path_existente:
            print(f"  [usando cópia já disponível] {path_existente}")
            return path_existente
        print(f"  [aviso] não encontrado localmente nem no S3: {nome_local}")
        return None

    if meta_s3 is None:
        if path_existente:
            print(f"  [aviso] arquivo não está mais no S3, usando cópia local: {path_existente}")
            return path_existente
        print(f"  [aviso] não disponível ainda no ONS: {nome_local}")
        return None

    registro = manifest.get(chave)

    if path_existente is None:
        precisa_baixar = True
    elif registro is None:
        # já existe cópia local, mas nunca foi registrada no manifest — adota como base
        precisa_baixar = False
    else:
        precisa_baixar = (
            registro["etag"] != meta_s3["etag"]
            or registro["last_modified_utc"] != meta_s3["last_modified_utc"]
            or registro["size"] != meta_s3["size"]
        )

    if not precisa_baixar:
        manifest[chave] = {
            "etag": meta_s3["etag"],
            "last_modified_utc": meta_s3["last_modified_utc"],
            "size": meta_s3["size"],
        }
        print(f"  [sem mudança no ONS] {path_existente}")
        return path_existente

    if registro is not None:
        print(f"  [ONS atualizou este mês] baixando de novo: {meta_s3['key']}")
    else:
        print(f"  [baixando via S3] {meta_s3['key']}")

    try:
        resp = get_s3_client().get_object(Bucket=BUCKET_ONS, Key=meta_s3["key"])
        conteudo = resp["Body"].read()
        path_cache.parent.mkdir(parents=True, exist_ok=True)
        path_cache.write_bytes(conteudo)
        print(f"  [ok] {nome_cache} ({path_cache.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"  [erro ao baixar do S3] {e}")
        if path_existente:
            print(f"  [usando cópia já disponível] {path_existente}")
            return path_existente
        return None

    manifest[chave] = {
        "etag": meta_s3["etag"],
        "last_modified_utc": meta_s3["last_modified_utc"],
        "size": meta_s3["size"],
    }
    return path_cache


def limpar_nome_conjunto(s: str) -> str:
    return re.sub(r"^CONJ\.\s*", "", str(s), flags=re.IGNORECASE).strip()


# ─── Processamento de um mês/fonte ───────────────────────────────────────────

def processar_mes(ano: int, mes: int, fonte: str, so_local: bool, manifest: dict, cadastro_ponto: dict) -> dict | None:
    label = f"{ano}-{mes:02d}"

    path_conj   = obter_arquivo(ano, mes, fonte, "conj",   so_local, manifest)
    path_detail = obter_arquivo(ano, mes, fonte, "detail", so_local, manifest)

    if path_conj is None:
        return None

    print(f"  [processando] {label} {fonte} ...")

    # Leitura
    conj = pd.read_parquet(path_conj, engine="fastparquet")
    det  = pd.read_parquet(path_detail, engine="fastparquet") if path_detail else None

    # Numérico
    for col in ["val_geracao", "val_geracaolimitada", "val_disponibilidade",
                "val_geracaoreferencia", "val_geracaoreferenciafinal"]:
        if col in conj.columns:
            conj[col] = pd.to_numeric(conj[col], errors="coerce").fillna(0)

    # Campos derivados
    conj["corte_mwh"] = (conj["val_geracaoreferencia"] - conj["val_geracao"]).clip(lower=0) * 0.5
    conj["tipo"]      = conj["cod_razaorestricao"].str.strip().replace("", pd.NA).fillna("SEM_RESTRICAO")
    conj["data"]      = conj["din_instante"].dt.date.astype(str)
    conj["mes"]       = label
    conj["fonte"]     = fonte
    conj["_key"]      = conj["nom_usina"].str.upper().str.strip()
    conj["ponto_cx"]  = conj["nom_usina"].apply(limpar_nome_conjunto)
    conj["id_ons_str"] = conj["id_ons"].astype(str).str.strip() if "id_ons" in conj.columns else ""

    # Ponto de conexão (subestação) — vem de um cadastro auxiliar, ligado pelo
    # id_ons, buscado sob demanda no dataset "Fator de Capacidade" do ONS.
    if not so_local and "id_ons" in conj.columns:
        ids_necessarios = conj["id_ons_str"].unique().tolist()
        atualizar_cadastro_ponto_conexao(cadastro_ponto, fonte, ano, mes, ids_necessarios)

    conj["ponto_conexao"] = conj["id_ons_str"].map(
        lambda i: cadastro_ponto.get((fonte, i), "Sem cadastro")
    )

    # Geração para o cálculo de percentual (igual ONS): total de referência =
    # geração verificada + GNRa contabilizada (só ENE/CNF/REL, mesmo critério do corte).
    conj["geracao_mwh"]     = conj["val_geracao"] * 0.5
    conj["corte_contab_mwh"] = conj["corte_mwh"].where(conj["tipo"].isin(["ENE", "CNF", "REL"]), 0.0)

    com_corte = conj[conj["tipo"].isin(["ENE", "CNF", "REL"])].copy()
    tem_corte = not com_corte.empty

    if not tem_corte:
        # Importante: NÃO retornar None aqui. Mesmo sem corte classificado (ENE/CNF/
        # REL) neste mês/fonte, a geração verificada é real e precisa entrar no total
        # de referência (usado no cálculo do percentual). Retornar None antes fazia
        # essa fonte desaparecer também da geração, não só do corte — o que deixava
        # o percentual sempre igual, mesmo alternando o filtro de fonte no dashboard.
        print(f"  [aviso] nenhum corte classificado (ENE/CNF/REL) em {label} {fonte} — geração ainda entra no total de referência")

    # Agregações — vazias quando não há corte classificado, mas o processamento continua
    if tem_corte:
        # Inclui conjunto/estado/subsistema/ponto de conexão na quebra diária (não só
        # mes/fonte/data/tipo) para que o gráfico de tendência no modo "um único mês"
        # também responda aos filtros de conjunto/estado/subsistema/ponto de conexão.
        diario = (com_corte.groupby(["mes","fonte","data","nom_subsistema","nom_estado","ponto_conexao","ponto_cx","tipo"])["corte_mwh"]
                  .sum().reset_index()
                  .rename(columns={"ponto_cx":"conjunto"})
                  .to_dict(orient="records"))

        mensal_conj = (com_corte.groupby(["mes","fonte","nom_subsistema","nom_estado","ponto_conexao","ponto_cx","tipo"])["corte_mwh"]
                       .sum().reset_index()
                       .rename(columns={"ponto_cx":"conjunto"})
                       .to_dict(orient="records"))

        mensal_estado = (com_corte.groupby(["mes","fonte","nom_subsistema","nom_estado","tipo"])["corte_mwh"]
                         .sum().reset_index().to_dict(orient="records"))

        mensal_total = (com_corte.groupby(["mes","fonte","tipo"])["corte_mwh"]
                        .sum().reset_index().to_dict(orient="records"))
    else:
        diario = []
        mensal_conj = []
        mensal_estado = []
        mensal_total = []

    # Geração de referência por ponto de conexão (sem quebra por tipo — usada só
    # para calcular o percentual do corte sobre o total gerado, igual ao ONS).
    # Usa TODO o "conj" (não só com_corte), porque a geração verificada existe
    # em toda hora, com ou sem restrição.
    mensal_conj_geracao = (
        conj.groupby(["mes", "fonte", "nom_subsistema", "nom_estado", "ponto_conexao", "ponto_cx"])
        .agg(geracao_mwh=("geracao_mwh", "sum"), corte_contab_mwh=("corte_contab_mwh", "sum"))
        .reset_index()
    )
    mensal_conj_geracao["referencia_mwh"] = (
        mensal_conj_geracao["geracao_mwh"] + mensal_conj_geracao["corte_contab_mwh"]
    )
    mensal_conj_geracao = (
        mensal_conj_geracao.drop(columns=["corte_contab_mwh"])
        .rename(columns={"ponto_cx": "conjunto"})
        .to_dict(orient="records")
    )

    # Geração de referência por dia, com a mesma quebra por conjunto/estado/
    # subsistema/ponto de conexão do "diario" acima — usada para o percentual no
    # gráfico e no tooltip, agora respeitando esses filtros também no modo diário.
    diario_geracao = (
        conj.groupby(["mes", "fonte", "data", "nom_subsistema", "nom_estado", "ponto_conexao", "ponto_cx"])
        .agg(geracao_mwh=("geracao_mwh", "sum"), corte_contab_mwh=("corte_contab_mwh", "sum"))
        .reset_index()
    )
    diario_geracao["referencia_mwh"] = (
        diario_geracao["geracao_mwh"] + diario_geracao["corte_contab_mwh"]
    )
    diario_geracao = (
        diario_geracao.drop(columns=["corte_contab_mwh"])
        .rename(columns={"ponto_cx": "conjunto"})
        .to_dict(orient="records")
    )

    # Usinas
    mensal_usinas = []
    mensal_usinas_geracao = []
    if det is not None:
        for col in ["val_geracaoestimada","val_geracaoverificada"]:
            if col in det.columns:
                det[col] = pd.to_numeric(det[col], errors="coerce").fillna(0)

        det["corte_usina_mwh"] = (det["val_geracaoestimada"] - det["val_geracaoverificada"]).clip(lower=0) * 0.5
        det["data"] = det["din_instante"].dt.date.astype(str)
        det["_key"] = det["nom_conjuntousina"].str.upper().str.strip()

        meta = conj[["_key","nom_subsistema","nom_estado","ponto_conexao","ponto_cx"]].drop_duplicates()

        if tem_corte:
            tipo_dom = (com_corte.groupby(["_key","data"])
                        .apply(lambda x: x.loc[x["corte_mwh"].idxmax(),"tipo"]
                               if x["corte_mwh"].sum() > 0 else "ENE",
                               include_groups=False)
                        .reset_index().rename(columns={0:"tipo"}))

            det2 = det.merge(tipo_dom, on=["_key","data"], how="inner")
            det2["mes"]   = label
            det2["fonte"] = fonte
            det2 = det2.merge(meta, on="_key", how="left")

            mensal_usinas = (det2.groupby(["mes","fonte","nom_subsistema","nom_estado","ponto_conexao","ponto_cx","nom_usina","tipo"])["corte_usina_mwh"]
                             .sum().reset_index()
                             .rename(columns={"nom_usina":"usina","corte_usina_mwh":"corte_mwh","ponto_cx":"conjunto"})
                             .to_dict(orient="records"))
            # OBS: quebra por usina no nível diário foi testada e descartada — o
            # volume de dados (dezenas de milhares de linhas por mês) deixaria o
            # dashboard com centenas de MB. O filtro de usina continua funcionando
            # nos KPIs/tabelas e na visão mensal agregada (mensal_usinas acima);
            # no gráfico de tendência (diário/mensal), o filtro mais fino disponível
            # é o de conjunto (ponto_cx), não usina individual.

        # Geração de referência por usina (sem quebra por tipo). Usa o "det" inteiro
        # (não o det2 filtrado pelo join com tipo_dom), porque toda usina/dia tem
        # geração verificada, mesmo nos dias sem corte.
        det_geracao = det.merge(meta, on="_key", how="left")
        det_geracao["mes"]   = label
        det_geracao["fonte"] = fonte
        det_geracao["geracao_mwh"]    = det_geracao["val_geracaoverificada"] * 0.5
        det_geracao["referencia_mwh"] = det_geracao["val_geracaoestimada"] * 0.5

        mensal_usinas_geracao = (
            det_geracao.groupby(["mes","fonte","nom_subsistema","nom_estado","ponto_conexao","ponto_cx","nom_usina"])
            .agg(geracao_mwh=("geracao_mwh","sum"), referencia_mwh=("referencia_mwh","sum"))
            .reset_index()
            .rename(columns={"nom_usina":"usina","ponto_cx":"conjunto"})
            .to_dict(orient="records")
        )

    # Horas reais com dado no parquet deste mês/fonte — não usar calendar.monthrange
    # aqui, porque para o mês corrente (ainda em andamento) isso contaria horas
    # futuras que ainda não existem no arquivo do ONS, diluindo o MW médio.
    horas_reais = int(conj["din_instante"].dt.floor("h").nunique())

    return {
        "horas":  horas_reais,
        "diario": diario,
        "conj":   mensal_conj,
        "estado": mensal_estado,
        "total":  mensal_total,
        "usinas": mensal_usinas,
        "conj_geracao":   mensal_conj_geracao,
        "usinas_geracao": mensal_usinas_geracao,
        "diario_geracao": diario_geracao,
    }


# ─── Logo ─────────────────────────────────────────────────────────────────────

def carregar_logo() -> str:
    """Retorna tag <img> com logo em base64, ou string vazia se não encontrar."""
    for nome in ["logo.png","logo.svg","logo.jpg","logo.jpeg","FSET.png","fset.png","fset.svg",
                 "logo FSET fundo transparente.png","logo FSET.png","FSET logo.png"]:
        p = DIR_LOCAL / nome
        if p.exists():
            mime = "image/svg+xml" if nome.endswith(".svg") else f"image/{nome.split('.')[-1]}"
            b64  = base64.b64encode(p.read_bytes()).decode()
            print(f"  [logo] {nome} incorporada no dashboard")
            return f'<img src="data:{mime};base64,{b64}" style="height:52px;max-width:160px;object-fit:contain;filter:brightness(1.05)">'
    return ""


# ─── Template HTML ────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>C-OFF Geração — ONS | FSET</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
  /* Paleta RegDesk: fundo slate-100, painéis brancos, header em gradiente
     azul-marinho, accent verde-sálvia. Ver DESIGN_SYSTEM.md. */
  :root{--bg:#f1f5f9;--card:#ffffff;--card-border:#f1f5f9;--border:#e2e8f0;
        --input-bg:#f8fafc;--text:#1e293b;--sub:#64748b;--meta:#94a3b8;
        --navy:#2b3f56;--navy-hover:#3a5570;--link:#3f5b70;
        --accent:#9FBE86;--accent-hover:#adca97;
        --ene:#c2410c;--cnf:#1d4ed8;--rel:#b91c1c;
        --shadow-sm:0 1px 3px rgba(43,63,86,.08),0 1px 2px rgba(43,63,86,.04);
        --shadow-md:0 4px 10px rgba(43,63,86,.12);
        --shadow-lg:0 10px 24px rgba(29,43,56,.22);}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Nunito Sans',sans-serif;
       font-weight:400;font-size:14px;display:flex;flex-direction:column;gap:16px;padding:20px;
       -webkit-font-smoothing:antialiased}
  h1{font-size:1.2rem;font-weight:800;color:#fff;letter-spacing:-.01em}
  h2{font-size:.82rem;font-weight:700;color:var(--sub);text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px}
  .header{background:linear-gradient(135deg,#3a5570 0%,#2b3f56 45%,#1d2b38 100%);
          border-radius:24px;padding:0 24px;box-shadow:var(--shadow-lg);
          display:flex;align-items:stretch;gap:14px;min-height:90px}
  .header-left{display:flex;align-items:center;gap:14px;flex:1;flex-wrap:wrap;padding:14px 0}
  .badge{background:rgba(255,255,255,.15);color:#fff;font-size:.7rem;font-weight:700;
         padding:3px 10px;border-radius:999px;white-space:nowrap;letter-spacing:.03em}
  .header-right{display:flex;align-items:stretch;gap:0;margin-left:auto}
  .gen-ts-wrap{display:flex;align-items:center;padding:0 20px;color:#cbd5e1;font-size:.75rem;
               border-left:1px solid rgba(255,255,255,.12)}
  .header-logo{display:flex;align-items:center;justify-content:center;flex:0 0 180px;
               border-left:1px solid rgba(255,255,255,.12);overflow:hidden}
  .gen-ts{color:#cbd5e1;font-size:.75rem}
  .filters{background:var(--card);border:1px solid var(--card-border);border-radius:24px;
           box-shadow:var(--shadow-sm);padding:14px 20px;
           display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end}
  .fgroup{display:flex;flex-direction:column;gap:3px}
  .fgroup label{font-size:.68rem;color:var(--sub);font-weight:700;text-transform:uppercase;letter-spacing:.06em}
  select,input[type=text]{background:var(--input-bg);border:1px solid var(--border);color:var(--text);
               padding:6px 10px;border-radius:16px;font-size:.83rem;outline:none;cursor:pointer;
               font-family:inherit;transition:.15s}
  select:focus,input:focus{border-color:var(--accent);background:#fff}
  .btn-limpar{background:#fff;border:1px solid var(--border);color:var(--sub);
    padding:6px 14px;border-radius:16px;font-size:.8rem;font-weight:700;cursor:pointer;white-space:nowrap;transition:.15s}
  .btn-limpar:hover{border-color:#fca5a5;color:#b91c1c;background:#fef2f2}
  .tog-btns{display:flex;gap:5px}
  .tog-btn{padding:5px 12px;border-radius:999px;border:1.5px solid var(--border);cursor:pointer;
           font-size:.78rem;font-weight:700;background:#fff;color:var(--sub);transition:.15s}
  .tog-btn.on-ENE{border-color:#fed7aa;background:#ffedd5;color:var(--ene)}
  .tog-btn.on-CNF{border-color:#bfdbfe;background:#dbeafe;color:var(--cnf)}
  .tog-btn.on-REL{border-color:#fecaca;background:#fee2e2;color:var(--rel)}
  .tog-btn.on-UFV{border-color:#fde68a;background:#fef3c7;color:#b45309}
  .tog-btn.on-EOL{border-color:#a7f3d0;background:#d1fae5;color:#047857}
  .tog-btn.on-mes{border-color:#c7d2fe;background:#e0e7ff;color:#4338ca}
  .msel{position:relative;display:inline-block}
  .msel-btn{background:var(--input-bg);border:1px solid var(--border);color:var(--text);
    padding:6px 10px;border-radius:16px;font-size:.83rem;cursor:pointer;font-family:inherit;
    white-space:nowrap;min-width:170px;text-align:left;width:100%;transition:.15s}
  .msel-btn:focus,.msel-btn:hover{border-color:var(--accent)}
  .msel-panel{position:absolute;top:calc(100% + 4px);left:0;z-index:200;
    background:#fff;border:1px solid var(--card-border);border-radius:14px;
    padding:5px 4px;min-width:140px;max-height:260px;overflow-y:auto;
    box-shadow:var(--shadow-md);display:none}
  .msel-item{display:flex;align-items:center;gap:8px;padding:5px 10px;
    border-radius:8px;cursor:pointer;font-size:.83rem;user-select:none;color:var(--text)}
  .msel-item:hover{background:#f8fafc}
  .msel-item input[type=checkbox]{accent-color:var(--accent);cursor:pointer;width:13px;height:13px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .card{background:var(--card);border:1px solid var(--card-border);border-radius:24px;
        padding:18px;box-shadow:var(--shadow-sm)}
  .card.full{grid-column:1/-1}
  .sec-title{display:flex;align-items:center;gap:10px;margin-bottom:10px}
  .sec-title h2{margin-bottom:0}
  .sec-num{flex:0 0 auto;width:28px;height:28px;border-radius:10px;background:var(--navy);
    color:#fff;font-size:.72rem;font-weight:800;display:flex;align-items:center;justify-content:center}
  .kpis{grid-column:1/-1;display:flex;gap:12px;flex-wrap:wrap}
  .kpi{flex:1;min-width:145px;background:var(--card);border:1px solid var(--card-border);
       border-radius:16px;padding:12px 15px;box-shadow:var(--shadow-sm)}
  .kpi .val{font-size:1.35rem;font-weight:800;margin-top:3px;color:var(--navy)}
  .kpi .lbl{color:var(--sub);font-size:.75rem;font-weight:600}
  .kpi.ene .val{color:var(--ene)}.kpi.cnf .val{color:var(--cnf)}.kpi.rel .val{color:var(--rel)}
  table{width:100%;border-collapse:collapse;font-size:.81rem}
  thead th{color:var(--sub);text-align:left;padding:6px 7px;border-bottom:1px solid var(--card-border);
           font-weight:700;font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}
  tbody tr:hover{background:#f8fafc}
  tbody td{padding:7px 7px;border-bottom:1px solid var(--card-border);color:var(--text)}
  .bar{background:#eef2f6;border-radius:3px;height:6px;width:100%}
  .bar-fill{height:6px;border-radius:3px}
  .dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;vertical-align:middle}
  .fonte-tag{font-size:.65rem;padding:2px 7px;border-radius:999px;font-weight:800;border:1px solid transparent}
  .ft-UFV{background:#fef3c7;color:#b45309;border-color:#fde68a}
  .ft-EOL{background:#d1fae5;color:#047857;border-color:#a7f3d0}
  .footer{font-size:.68rem;color:var(--meta);padding:2px 4px}
  *{scrollbar-color:rgb(203 213 225) transparent}
  *::-webkit-scrollbar{width:10px;height:10px}
  *::-webkit-scrollbar-thumb{background-color:rgb(203 213 225);border-radius:9999px}
  *::-webkit-scrollbar-thumb:hover{background-color:rgb(148 163 184)}
  @media(max-width:700px){.grid{grid-template-columns:1fr}.card.full{grid-column:1}}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>⚡ C-OFF Geração</h1>
    <span class="badge">ONS Dados Abertos</span>
  </div>
  <div class="header-right">
    <div class="gen-ts-wrap">Gerado em __GERADO_EM__</div>
    <div class="header-logo">__LOGO__</div>
  </div>
</div>

<div class="filters">
  <div class="fgroup">
    <label>Ano</label>
    <div class="msel" id="anoWrap">
      <button class="msel-btn" id="anoBtn" type="button">Todos os anos ▾</button>
      <div class="msel-panel" id="anoPanel"></div>
    </div>
  </div>
  <div class="fgroup">
    <label>Mês</label>
    <div class="msel" id="mesWrap">
      <button class="msel-btn" id="mesBtn" type="button">Todos os meses ▾</button>
      <div class="msel-panel" id="mesPanel"></div>
    </div>
  </div>
  <div class="fgroup">
    <label>Fonte</label>
    <div class="tog-btns" id="btnsFonte"></div>
  </div>
  <div class="fgroup">
    <label>Tipo de corte</label>
    <div class="tog-btns">
      <button class="tog-btn on-ENE" data-tipo="ENE" onclick="toggleTipo(this)">ENE</button>
      <button class="tog-btn on-CNF" data-tipo="CNF" onclick="toggleTipo(this)">CNF</button>
      <button class="tog-btn on-REL" data-tipo="REL" onclick="toggleTipo(this)">REL</button>
    </div>
  </div>
  <div class="fgroup">
    <label>Subsistema</label>
    <select id="selSub"><option value="">Todos</option></select>
  </div>
  <div class="fgroup">
    <label>Estado</label>
    <select id="selEstado"><option value="">Todos</option></select>
  </div>
  <div class="fgroup">
    <label>Ponto de conexão</label>
    <select id="selPonto" style="width:190px"><option value="">Todos</option></select>
  </div>
  <div class="fgroup">
    <label>Conjunto de usinas</label>
    <select id="selConj" style="width:210px"><option value="">Todos</option></select>
  </div>
  <div class="fgroup">
    <label>Usina</label>
    <select id="selUsina" style="width:210px" disabled><option value="">— selecione um conjunto —</option></select>
  </div>
  <div class="fgroup" style="margin-left:auto">
    <label>&nbsp;</label>
    <button class="btn-limpar" id="btnLimpar" type="button" onclick="limparFiltros()">✕ Limpar filtros</button>
  </div>
</div>

<div class="grid">
  <div class="kpis" id="kpis"></div>

  <div class="card full">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:10px">
      <div class="sec-title" style="margin-bottom:0">
        <div class="sec-num">01</div>
        <h2 style="margin-bottom:0" id="tituloTendencia">Tendência Diária (MW médios)</h2>
      </div>
      <button class="btn-limpar" type="button" onclick="exportarCSV()">⭳ Exportar CSV</button>
    </div>
    <canvas id="chartDiario" height="80"></canvas>
  </div>

  <div class="card">
    <div class="sec-title"><div class="sec-num">02</div><h2>Top Conjunto de Usinas</h2></div>
    <div style="overflow-y:auto;max-height:420px">
      <table id="tblConj">
        <thead><tr>
          <th>Conjunto</th><th>Fonte</th><th>UF</th><th>Tipo</th>
          <th>MW méd</th><th style="width:85px">Part.</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="sec-title"><div class="sec-num">03</div><h2>Distribuição por Estado</h2></div>
    <div style="height:420px">
      <canvas id="chartEstado"></canvas>
    </div>
  </div>

  <div class="card full">
    <div class="sec-title"><div class="sec-num">04</div><h2>Top Usinas</h2></div>
    <div style="overflow-y:auto;max-height:360px">
      <table id="tblUsinas">
        <thead><tr>
          <th>#</th><th>Usina</th><th>Conjunto</th><th>Fonte</th>
          <th>UF</th><th>Tipo</th><th>MW méd</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</div>
<div class="footer">Fonte: ONS Dados Abertos — restricao_coff_fotovoltaica / restricao_coff_eolica</div>

<script>
const DATA = __DATA_JSON__;

let anosSel     = new Set();  // Set de anos "YYYY"; vazio = todos
let mesesNumSel = new Set();  // Set de números 1-12; vazio = todos
let fontesAt    = new Set(DATA.meta.fontes_disponiveis);
let tiposAt     = new Set(['ENE','CNF','REL']);
let subSel = '', estSel = '', pontoSel = '', conjSel = '', usinaSel = '';

const COR   = {ENE:'#c2410c',CNF:'#1d4ed8',REL:'#b91c1c'};
const NOMES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
const sel   = id => document.getElementById(id);

// Meses (YYYY-MM) que passam pelos dois filtros
function mesesAtivos(){
  return DATA.meta.meses_disponiveis.filter(m => {
    const aOk = anosSel.size === 0 || anosSel.has(m.slice(0,4));
    const mOk = mesesNumSel.size === 0 || mesesNumSel.has(parseInt(m.slice(5,7)));
    return aOk && mOk;
  });
}

function filtroBase(r){
  const aOk = anosSel.size === 0 || anosSel.has(r.mes.slice(0,4));
  const mOk = mesesNumSel.size === 0 || mesesNumSel.has(parseInt(r.mes.slice(5,7)));
  return aOk && mOk && fontesAt.has(r.fonte) && tiposAt.has(r.tipo)
      && (!subSel||r.nom_subsistema===subSel) && (!estSel||r.nom_estado===estSel)
      && (!pontoSel||r.ponto_conexao===pontoSel);
}
function filtroConj(r){
  return filtroBase(r) && (!conjSel || r.conjunto === conjSel);
}
function filtroUsina(r){
  return filtroBase(r)
      && (!conjSel  || r.conjunto === conjSel)
      && (!usinaSel || r.usina    === usinaSel);
}

// Mesmos filtros de período/fonte/subsistema/estado/conjunto/usina, mas sem
// filtro de "tipo" — usados nos dados de geração (que não têm quebra por tipo),
// para calcular o percentual do corte sobre o total gerado, igual ao ONS.
function filtroGeracaoBase(r){
  const aOk = anosSel.size === 0 || anosSel.has(r.mes.slice(0,4));
  const mOk = mesesNumSel.size === 0 || mesesNumSel.has(parseInt(r.mes.slice(5,7)));
  return aOk && mOk && fontesAt.has(r.fonte)
      && (!subSel||r.nom_subsistema===subSel) && (!estSel||r.nom_estado===estSel)
      && (!pontoSel||r.ponto_conexao===pontoSel)
      && (!conjSel||r.conjunto===conjSel);
}
function filtroGeracaoUsina(r){
  return filtroGeracaoBase(r) && (!usinaSel || r.usina === usinaSel);
}

function referenciaTotal(){
  const rows = usinaSel
    ? DATA.mensal_usinas_geracao.filter(filtroGeracaoUsina)
    : DATA.mensal_conjunto_geracao.filter(filtroGeracaoBase);
  return rows.reduce((s,r)=>s+r.referencia_mwh, 0);
}

// Referência (geração + GNRa) para um dia/mês específico, só por fonte — mesmo
// recorte que o gráfico de tendência já usa (não aplica subsistema/estado/conjunto,
// porque o gráfico em si também não aplica). Usado só para o percentual no tooltip.
// Nota: não há quebra por usina no nível diário (o volume de dados inviabiliza
// embutir isso no HTML — testado e descartado, ver comentário em processar_mes()
// no .py). Por isso aqui usamos sempre filtroGeracaoBase (conjunto/estado/
// subsistema/ponto), mesmo com uma usina específica selecionada.
function referenciaDia(mesX, diaX){
  return DATA.diario_geracao
    .filter(r=>r.mes===mesX && r.data===diaX && filtroGeracaoBase(r))
    .reduce((s,r)=>s+r.referencia_mwh, 0);
}
function referenciaMes(mesX){
  const rows = usinaSel
    ? DATA.mensal_usinas_geracao.filter(r=>r.mes===mesX && filtroGeracaoUsina(r))
    : DATA.mensal_conjunto_geracao.filter(r=>r.mes===mesX && filtroGeracaoBase(r));
  return rows.reduce((s,r)=>s+r.referencia_mwh, 0);
}

// Exporta os dados por trás do gráfico de tendência (diário ou mensal, conforme
// o período selecionado) em CSV, no padrão que o Excel PT-BR espera: separador
// ";", decimal com vírgula, e BOM UTF-8 pra acentos aparecerem certo.
function csvNum(v){
  if(v===''||v===null||v===undefined||isNaN(v)) return '';
  return Number(v).toFixed(2).replace('.',',');
}

function exportarCSV(){
  const ma = mesesAtivos();
  const tipos = ['ENE','CNF','REL'];
  const cabecalho = ['Período','ENE (MW médio)','CNF (MW médio)','REL (MW médio)','Total (MW médio)',
                      'ENE (%)','CNF (%)','REL (%)','Total (%)'];
  let linhas = [];
  let nomeArquivo = 'tendencia.csv';

  if(ma.length <= 1){
    const mes1 = ma[0] || '';
    const dias=[...new Set(DATA.diario_tipo.filter(r=>r.mes===mes1).map(r=>r.data))].sort();
    const byCT={};
    DATA.diario_tipo.filter(r=>r.mes===mes1&&filtroGeracaoBase(r))
      .forEach(r=>{if(!byCT[r.tipo])byCT[r.tipo]={};byCT[r.tipo][r.data]=(byCT[r.tipo][r.data]||0)+r.corte_mwh;});

    linhas = dias.map(d=>{
      const refMwh = referenciaDia(mes1, d);
      const valsMwh = tipos.map(t=>(byCT[t]||{})[d]||0);
      const totalMwh = valsMwh.reduce((a,b)=>a+b,0);
      const mws = valsMwh.map(v=>v/24);
      const totalMw = totalMwh/24;
      const pcts = valsMwh.map(v=> refMwh>0 ? v/refMwh*100 : '');
      const totalPct = refMwh>0 ? totalMwh/refMwh*100 : '';
      return [d, ...mws.map(csvNum), csvNum(totalMw), ...pcts.map(csvNum), csvNum(totalPct)];
    });
    nomeArquivo = 'tendencia_diaria_'+(mes1||'periodo')+'.csv';
  } else {
    // Precisa usar o MESMO escopo do referenciaMes() (usina, quando selecionada,
    // senão conjunto) — senão o numerador (corte) e o denominador (referência)
    // vêm de recortes diferentes e o percentual estoura acima de 100%.
    const byCTM={};
    const srcCSVm = usinaSel ? DATA.mensal_usinas : DATA.diario_tipo;
    const fCSVm   = usinaSel ? filtroGeracaoUsina : filtroGeracaoBase;
    srcCSVm.filter(fCSVm).forEach(r=>{
      if(!byCTM[r.tipo]) byCTM[r.tipo]={};
      byCTM[r.tipo][r.mes]=(byCTM[r.tipo][r.mes]||0)+r.corte_mwh;
    });

    linhas = ma.map(m=>{
      const refMwh = referenciaMes(m);
      const H = DATA.meta.horas_por_mes[m]||720;
      const valsMwh = tipos.map(t=>(byCTM[t]||{})[m]||0);
      const totalMwh = valsMwh.reduce((a,b)=>a+b,0);
      const mws = valsMwh.map(v=>v/H);
      const totalMw = totalMwh/H;
      const pcts = valsMwh.map(v=> refMwh>0 ? v/refMwh*100 : '');
      const totalPct = refMwh>0 ? totalMwh/refMwh*100 : '';
      return [fmtMes(m), ...mws.map(csvNum), csvNum(totalMw), ...pcts.map(csvNum), csvNum(totalPct)];
    });
    nomeArquivo = 'tendencia_mensal_'+(ma[0]||'inicio')+'_a_'+(ma[ma.length-1]||'fim')+'.csv';
  }

  const escapar = c => (typeof c==='string' && (c.includes(';')||c.includes('"')))
    ? '"'+c.replace(/"/g,'""')+'"' : c;
  const corpo = [cabecalho, ...linhas].map(l=>l.map(escapar).join(';')).join('\r\n');

  const blob = new Blob(['﻿'+corpo], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nomeArquivo;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function horasPeriodo(){
  const h = mesesAtivos().reduce((s,m) => s + (DATA.meta.horas_por_mes[m]||720), 0);
  return h || 720;
}

function fmt1(v){
  const n = Number(v)||0;
  const neg = n < 0;
  const [intPart, decPart] = Math.abs(n).toFixed(1).split('.');
  const intFmt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return (neg?'-':'') + intFmt + ',' + decPart;
}
function fmtInt(v){
  const n = Math.round(Number(v)||0);
  const neg = n < 0;
  return (neg?'-':'') + Math.abs(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}
function fmtMes(m){
  const [a,ms]=m.split('-').map(Number);
  return NOMES[ms-1]+'/'+a;
}
function labelPeriodo(){
  const ma = mesesAtivos();
  if(ma.length === 0) return 'Nenhum mês';
  if(ma.length === 1) return fmtMes(ma[0]) + ' (' + fmtInt(horasPeriodo()) + 'h)';
  return ma.length + ' meses (' + fmtInt(horasPeriodo()) + 'h)';
}

function mesesDisponiveis(){
  return new Set(
    DATA.meta.meses_disponiveis
      .filter(m => anosSel.size === 0 || anosSel.has(m.slice(0,4)))
      .map(m => parseInt(m.slice(5,7)))
  );
}

function atualizaMesBtn(){
  const btn = sel('mesBtn');
  const disp = mesesDisponiveis();
  const sel_nomes = NOMES.filter((_,i) => mesesNumSel.has(i+1) && disp.has(i+1));
  btn.textContent = sel_nomes.length === 0 ? 'Todos os meses ▾' : sel_nomes.join(', ') + ' ▾';
}

function populaBtnsMes(){
  const panel = sel('mesPanel');
  panel.innerHTML = '';
  [...mesesDisponiveis()].sort((a,b)=>a-b).forEach(num => {
    const nome = NOMES[num-1];
    const item = document.createElement('label');
    item.className = 'msel-item';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = mesesNumSel.has(num);
    cb.onchange = () => {
      if(cb.checked) mesesNumSel.add(num);
      else           mesesNumSel.delete(num);
      atualizaMesBtn();
      populaConjs();
      render();
    };
    item.appendChild(cb);
    item.appendChild(document.createTextNode(' ' + nome));
    panel.appendChild(item);
  });
  atualizaMesBtn();
}

sel('mesBtn') && sel('mesBtn').addEventListener('click', e => {
  e.stopPropagation();
  const p = sel('mesPanel');
  p.style.display = p.style.display === 'none' ? 'block' : 'none';
});
document.addEventListener('click', () => {
  const p = sel('mesPanel');
  if(p) p.style.display = 'none';
  const pa = sel('anoPanel');
  if(pa) pa.style.display = 'none';
});

// Anos disponíveis no dataset, do mais recente para o mais antigo (independe
// de mesesNumSel — mostra sempre todos os anos que existem em algum mês).
function anosDisponiveis(){
  return [...new Set(DATA.meta.meses_disponiveis.map(m=>m.slice(0,4)))].sort().reverse();
}

function atualizaAnoBtn(){
  const btn = sel('anoBtn');
  const sel_anos = anosDisponiveis().filter(a => anosSel.has(a));
  btn.textContent = sel_anos.length === 0 ? 'Todos os anos ▾' : sel_anos.join(', ') + ' ▾';
}

function populaBtnsAno(){
  const panel = sel('anoPanel');
  panel.innerHTML = '';
  anosDisponiveis().forEach(a => {
    const item = document.createElement('label');
    item.className = 'msel-item';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = anosSel.has(a);
    cb.onchange = () => {
      if(cb.checked) anosSel.add(a);
      else           anosSel.delete(a);
      // Mudar o(s) ano(s) pode tornar o mês selecionado indisponível; limpa
      // a seleção de mês, igual ao comportamento anterior do select único.
      mesesNumSel.clear();
      atualizaAnoBtn();
      populaBtnsMes();
      populaConjs();
      render();
    };
    item.appendChild(cb);
    item.appendChild(document.createTextNode(' ' + a));
    panel.appendChild(item);
  });
  atualizaAnoBtn();
}

sel('anoBtn') && sel('anoBtn').addEventListener('click', e => {
  e.stopPropagation();
  const p = sel('anoPanel');
  p.style.display = p.style.display === 'none' ? 'block' : 'none';
});

function initFiltros(){
  // ── Ano (toggle multi-seleção, igual ao Mês) ──
  populaBtnsAno();

  // ── Meses (toggle Jan-Dez, independente do ano) ──
  populaBtnsMes();

  // ── Fonte ──
  const etiq = {UFV:'☀️ Solar', EOL:'💨 Eólica'};
  DATA.meta.fontes_disponiveis.forEach(f => {
    const btn = document.createElement('button');
    btn.className = 'tog-btn on-' + f;
    btn.dataset.fonte = f;
    btn.textContent = etiq[f] || f;
    btn.onclick = () => toggleFonte(btn);
    sel('btnsFonte').appendChild(btn);
  });

  // ── Subsistemas, estados, pontos de conexão, conjuntos ──
  const subs = [...new Set(DATA.mensal_conjunto.map(r=>r.nom_subsistema))].sort();
  subs.forEach(s => sel('selSub').add(new Option(s,s)));
  sel('selSub').onchange    = () => { subSel=sel('selSub').value; populaEstados(); populaPontos(); populaConjs(); render(); };
  populaEstados();
  sel('selEstado').onchange = () => { estSel=sel('selEstado').value; populaPontos(); populaConjs(); render(); };
  populaPontos();
  sel('selPonto').onchange = () => { pontoSel=sel('selPonto').value; populaConjs(); render(); };
  populaConjs();
  sel('selConj').onchange  = () => { conjSel=sel('selConj').value; populaUsinas(); render(); };
  sel('selUsina').onchange = () => { usinaSel=sel('selUsina').value; render(); };
}

function limparFiltros(){
  anosSel.clear();
  mesesNumSel.clear();
  fontesAt = new Set(DATA.meta.fontes_disponiveis);
  tiposAt  = new Set(['ENE','CNF','REL']);
  subSel = ''; estSel = ''; pontoSel = ''; conjSel = ''; usinaSel = '';

  populaBtnsAno();
  populaBtnsMes();

  document.querySelectorAll('#btnsFonte .tog-btn').forEach(btn=>{
    btn.classList.add('on-'+btn.dataset.fonte);
  });
  document.querySelectorAll('.tog-btn[data-tipo]').forEach(btn=>{
    btn.classList.add('on-'+btn.dataset.tipo);
  });

  sel('selSub').value = '';
  populaEstados();
  populaPontos();
  populaConjs(); // já chama populaUsinas() internamente
  render();
}

function populaEstados(){
  const dd=sel('selEstado'), prev=estSel;
  while(dd.options.length>1) dd.remove(1);
  const est=[...new Set(DATA.mensal_conjunto.filter(r=>!subSel||r.nom_subsistema===subSel).map(r=>r.nom_estado))].sort();
  est.forEach(e=>dd.add(new Option(e,e)));
  dd.value=est.includes(prev)?prev:''; estSel=dd.value;
}

function populaPontos(){
  const dd=sel('selPonto'), prev=pontoSel;
  while(dd.options.length>1) dd.remove(1);
  const pontos=[...new Set(DATA.mensal_conjunto
    .filter(r=>(!subSel||r.nom_subsistema===subSel)&&(!estSel||r.nom_estado===estSel))
    .map(r=>r.ponto_conexao))].sort();
  pontos.forEach(p=>dd.add(new Option(p,p)));
  dd.value=pontos.includes(prev)?prev:''; pontoSel=dd.value;
}

function populaConjs(){
  const dd=sel('selConj'), prev=conjSel;
  while(dd.options.length>1) dd.remove(1);
  const conjs=[...new Set(DATA.mensal_conjunto.filter(filtroBase).map(r=>r.conjunto))].sort();
  conjs.forEach(c=>dd.add(new Option(c,c)));
  dd.value=conjs.includes(prev)?prev:''; conjSel=dd.value;
  populaUsinas();
}

function populaUsinas(){
  const dd=sel('selUsina'), prev=usinaSel;
  dd.innerHTML='';
  if(!conjSel){
    dd.add(new Option('— selecione um conjunto —',''));
    dd.disabled=true; usinaSel=''; return;
  }
  dd.disabled=false;
  dd.add(new Option('Todas as usinas',''));
  const usinas=[...new Set(DATA.mensal_usinas
    .filter(r=>filtroBase(r)&&r.conjunto===conjSel)
    .map(r=>r.usina))].sort();
  usinas.forEach(u=>dd.add(new Option(u,u)));
  dd.value=usinas.includes(prev)?prev:''; usinaSel=dd.value;
}

function toggleFonte(btn){
  const f=btn.dataset.fonte;
  if(fontesAt.has(f)&&fontesAt.size===1) return;
  fontesAt.has(f)?(fontesAt.delete(f),btn.classList.remove('on-'+f)):(fontesAt.add(f),btn.classList.add('on-'+f));
  render();
}
function toggleTipo(btn){
  const t=btn.dataset.tipo;
  if(tiposAt.has(t)&&tiposAt.size===1) return;
  tiposAt.has(t)?(tiposAt.delete(t),btn.classList.remove('on-'+t)):(tiposAt.add(t),btn.classList.add('on-'+t));
  render();
}

let chartD=null, chartE=null;

function render(){
  const H  = horasPeriodo();
  const ma = mesesAtivos();

  // ── KPIs ──
  const tot={ENE:0,CNF:0,REL:0};
  // Quando uma usina específica está selecionada, usa dados de usinas; caso contrário, conjuntos
  if(usinaSel){
    DATA.mensal_usinas.filter(filtroUsina).forEach(r=>{tot[r.tipo]=(tot[r.tipo]||0)+r.corte_mwh;});
  } else {
    DATA.mensal_conjunto.filter(filtroConj).forEach(r=>{tot[r.tipo]=(tot[r.tipo]||0)+r.corte_mwh;});
  }
  const totalMW=Object.values(tot).reduce((a,b)=>a+b,0)/H;
  const kpiCtx = usinaSel ? usinaSel : labelPeriodo();

  // Percentual sobre o total de geração de referência (geração verificada + GNRa),
  // igual ao critério do dashboard oficial do ONS.
  const refTotal  = referenciaTotal();
  const totalCorte = tot.ENE+tot.CNF+tot.REL;
  const pct = v => refTotal>0 ? ' <span style="color:#64748b;font-weight:500">| '+fmt1(v/refTotal*100)+'%</span>' : '';

  sel('kpis').innerHTML=[
    {cls:'',   lbl:'Total — '+kpiCtx,          val:fmt1(totalMW)+' MW méd'+pct(totalCorte), sub:'todos os tipos selecionados'},
    {cls:'ene',lbl:'ENE — Energético',          val:fmt1((tot.ENE||0)/H)+' MW méd'+pct(tot.ENE||0), sub:''},
    {cls:'cnf',lbl:'CNF — Confiabilidade',      val:fmt1((tot.CNF||0)/H)+' MW méd'+pct(tot.CNF||0), sub:''},
    {cls:'rel',lbl:'REL — Indisponibilidade',   val:fmt1((tot.REL||0)/H)+' MW méd'+pct(tot.REL||0), sub:''},
  ].map(k=>'<div class="kpi '+k.cls+'"><div class="lbl">'+k.lbl+'</div><div class="val">'+k.val+'</div>'+(k.sub?'<div class="lbl">'+k.sub+'</div>':'')+'</div>').join('');

  // ── Tendência: diário (1 mês) ou mensal (vários) ──
  if(chartD) chartD.destroy();
  if(ma.length <= 1){
    // gráfico diário — diario_tipo agora tem quebra por conjunto/estado/
    // subsistema/ponto de conexão, então filtroConj já funciona aqui. Não há
    // quebra por usina no nível diário (ver nota em referenciaDia).
    const mes1 = ma[0] || '';
    const dias=[...new Set(DATA.diario_tipo.filter(r=>r.mes===mes1).map(r=>r.data))].sort();
    const byCT={};
    DATA.diario_tipo.filter(r=>r.mes===mes1&&filtroConj(r))
      .forEach(r=>{if(!byCT[r.tipo])byCT[r.tipo]={};byCT[r.tipo][r.data]=(byCT[r.tipo][r.data]||0)+r.corte_mwh;});
    const datasets=[...(tiposAt)].map(t=>({
      label:t, data:dias.map(d=>((byCT[t]||{})[d]||0)/24),
      borderColor:COR[t], backgroundColor:COR[t]+'33', fill:true, tension:.3, pointRadius:2
    }));
    chartD=new Chart(sel('chartDiario'),{type:'line',
      data:{labels:dias.map(d=>d.slice(5)),datasets},
      options:{responsive:true,interaction:{mode:'index',intersect:false},
        plugins:{
          legend:{labels:{color:'#475569',font:{size:11}}},
          tooltip:{callbacks:{label:ctx=>{
            const t = ctx.dataset.label;
            const d = dias[ctx.dataIndex];
            const corteMwh = (byCT[t]||{})[d]||0;
            const refMwh   = referenciaDia(mes1, d);
            const pctStr   = refMwh>0 ? ' ('+fmt1(corteMwh/refMwh*100)+'%)' : '';
            return ' '+t+': '+fmt1(ctx.parsed.y)+' MW méd'+pctStr;
          }}}
        },
        scales:{x:{ticks:{color:'#64748b',font:{size:10}},grid:{color:'#e2e8f0'}},
                y:{ticks:{color:'#64748b',font:{size:10},callback:v=>fmt1(v)},grid:{color:'#e2e8f0'},
                   title:{display:true,text:'MW médios',color:'#64748b',font:{size:10}}}}}});
  } else {
    // gráfico mensal agregado: barras por tipo (CNF/ENE/REL) + linha "Total"
    // com rótulo do percentual sobre a geração de referência (mesmo critério do ONS).
    // Fonte tem que casar com o escopo do referenciaMes() (usina, se selecionada,
    // senão conjunto) — do contrário numerador e denominador vêm de recortes
    // diferentes e o % passa de 100% (bug reportado: conjunto inteiro / 1 usina).
    const byCTM={};
    const srcMes = usinaSel ? DATA.mensal_usinas : DATA.diario_tipo;
    const fMes   = usinaSel ? filtroUsina : filtroConj;
    srcMes.filter(fMes).forEach(r=>{
      if(!byCTM[r.tipo]) byCTM[r.tipo]={};
      byCTM[r.tipo][r.mes]=(byCTM[r.tipo][r.mes]||0)+r.corte_mwh;
    });
    const datasets=[...(tiposAt)].map(t=>({
      type:'bar',
      label:t,
      data:ma.map(m=>((byCTM[t]||{})[m]||0)/(DATA.meta.horas_por_mes[m]||720)),
      backgroundColor:COR[t]+'cc', borderColor:COR[t], borderWidth:0, order:2
    }));
    // Total = soma dos tipos ativos no mês; percentual = total / geração de referência do mês
    // (mesma referência já usada no tooltip, reaproveitada aqui — nenhum número novo).
    const totalMWmes = ma.map(m=>{
      let s=0; [...tiposAt].forEach(t=>{s+=(byCTM[t]||{})[m]||0;});
      return s/(DATA.meta.horas_por_mes[m]||720);
    });
    const totalPct = ma.map(m=>{
      let s=0; [...tiposAt].forEach(t=>{s+=(byCTM[t]||{})[m]||0;});
      const ref = referenciaMes(m);
      return ref>0 ? s/ref*100 : null;
    });
    datasets.push({
      type:'line', label:'Total', data:totalMWmes,
      borderColor:'#2b3f56', backgroundColor:'#2b3f56',
      pointBackgroundColor:'#2b3f56', pointBorderColor:'#2b3f56',
      borderWidth:2, pointRadius:3, fill:false, tension:.25, order:1
    });
    const totalPctLabelsPlugin = {
      id:'totalPctLabels',
      afterDatasetsDraw(chart){
        const dsIndex = chart.data.datasets.findIndex(d=>d.label==='Total');
        if(dsIndex<0) return;
        if(!chart.isDatasetVisible(dsIndex)) return;
        const meta = chart.getDatasetMeta(dsIndex);
        const ctx = chart.ctx;
        ctx.save();
        ctx.fillStyle = '#2b3f56';
        ctx.font = 'bold 11px sans-serif';
        ctx.textAlign = 'center';
        meta.data.forEach((point,i)=>{
          const v = totalPct[i];
          if(v===null||v===undefined) return;
          ctx.fillText(fmt1(v)+'%', point.x, point.y-10);
        });
        ctx.restore();
      }
    };
    chartD=new Chart(sel('chartDiario'),{type:'bar',
      data:{labels:ma.map(fmtMes),datasets},
      plugins:[totalPctLabelsPlugin],
      options:{responsive:true,interaction:{mode:'index',intersect:false},
        layout:{padding:{top:18}},
        plugins:{
          legend:{labels:{color:'#475569',font:{size:11}}},
          tooltip:{callbacks:{label:ctx=>{
            if(ctx.dataset.label==='Total'){
              const m = ma[ctx.dataIndex];
              const pct = totalPct[ctx.dataIndex];
              const pctStr = (pct!==null&&pct!==undefined) ? ' ('+fmt1(pct)+'%)' : '';
              return ' Total: '+fmt1(ctx.parsed.y)+' MW méd'+pctStr;
            }
            const t = ctx.dataset.label;
            const m = ma[ctx.dataIndex];
            const corteMwh = (byCTM[t]||{})[m]||0;
            const refMwh   = referenciaMes(m);
            const pctStr   = refMwh>0 ? ' ('+fmt1(corteMwh/refMwh*100)+'%)' : '';
            return ' '+t+': '+fmt1(ctx.parsed.y)+' MW méd'+pctStr;
          }}}
        },
        scales:{x:{ticks:{color:'#64748b',font:{size:10}},grid:{color:'#e2e8f0'}},
                y:{ticks:{color:'#64748b',font:{size:10},callback:v=>fmt1(v)},grid:{color:'#e2e8f0'},
                   title:{display:true,text:'MW médios',color:'#64748b',font:{size:10}}}}}});
  }

  // ── Top pontos de conexão ──
  const agrC={};
  DATA.mensal_conjunto.filter(filtroConj).forEach(r=>{
    const k=r.fonte+'||'+r.conjunto;
    if(!agrC[k]) agrC[k]={conjunto:r.conjunto,fonte:r.fonte,uf:r.nom_estado,corte:0,tipos:{}};
    agrC[k].corte+=r.corte_mwh; agrC[k].tipos[r.tipo]=(agrC[k].tipos[r.tipo]||0)+r.corte_mwh;
  });
  const rowsC=Object.values(agrC).sort((a,b)=>b.corte-a.corte).slice(0,25);
  const maxC=rowsC[0]?.corte||1;
  sel('tblConj').querySelector('tbody').innerHTML=rowsC.map(r=>{
    const mw=r.corte/H, pct=(r.corte/maxC*100).toFixed(0);
    const tm=Object.entries(r.tipos).sort((a,b)=>b[1]-a[1])[0]?.[0]||'';
    return '<tr><td>'+r.conjunto+'</td>'
      +'<td><span class="fonte-tag ft-'+r.fonte+'">'+r.fonte+'</span></td>'
      +'<td>'+r.uf+'</td>'
      +'<td><span class="dot" style="background:'+(COR[tm]||'#64748b')+'"></span>'+tm+'</td>'
      +'<td>'+fmt1(mw)+'</td>'
      +'<td><div class="bar"><div class="bar-fill" style="width:'+pct+'%;background:'+(COR[tm]||'#6366f1')+'"></div></div></td>'
      +'</tr>';
  }).join('');

  // ── Distribuição por estado ──
  const agrE={};
  DATA.mensal_estado.filter(r=>{
    const aOk=anosSel.size===0||anosSel.has(r.mes.slice(0,4));
    const mOk=mesesNumSel.size===0||mesesNumSel.has(parseInt(r.mes.slice(5,7)));
    return aOk&&mOk&&fontesAt.has(r.fonte)&&tiposAt.has(r.tipo)
        &&(!subSel||r.nom_subsistema===subSel)&&(!estSel||r.nom_estado===estSel);
  }).forEach(r=>{
    if(!agrE[r.nom_estado]) agrE[r.nom_estado]={ENE:0,CNF:0,REL:0};
    agrE[r.nom_estado][r.tipo]=(agrE[r.nom_estado][r.tipo]||0)+r.corte_mwh;
  });
  const estats=Object.entries(agrE).sort((a,b)=>(b[1].ENE+b[1].CNF+b[1].REL)-(a[1].ENE+a[1].CNF+a[1].REL));

  if(chartE) chartE.destroy();
  chartE=new Chart(sel('chartEstado'),{type:'bar',
    data:{labels:estats.map(([e])=>e),
      datasets:['ENE','CNF','REL'].filter(t=>tiposAt.has(t)).map(t=>({
        label:t, data:estats.map(([,v])=>(v[t]||0)/H), backgroundColor:COR[t]+'cc'}))},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{labels:{color:'#475569',font:{size:11}}},
        tooltip:{callbacks:{label:ctx=>' '+ctx.dataset.label+': '+fmt1(ctx.parsed.x)+' MW méd'}}
      },
      scales:{
        x:{stacked:true,ticks:{color:'#64748b',font:{size:10},callback:v=>fmt1(v)},grid:{color:'#e2e8f0'}},
        y:{stacked:true,ticks:{color:'#64748b',font:{size:10}},grid:{color:'#e2e8f0'}}
      }}});

  // ── Top usinas ──
  const agrU={};
  DATA.mensal_usinas.filter(filtroUsina).forEach(r=>{
    const k=r.fonte+'||'+r.usina;
    if(!agrU[k]) agrU[k]={usina:r.usina,conjunto:r.conjunto,fonte:r.fonte,uf:r.nom_estado,corte:0,tipos:new Set()};
    agrU[k].corte+=r.corte_mwh;
    agrU[k].tipos.add(r.tipo);
  });
  const rowsU=Object.values(agrU).sort((a,b)=>b.corte-a.corte).slice(0,30);
  sel('tblUsinas').querySelector('tbody').innerHTML=rowsU.map((r,i)=>{
    const tipoLabel=r.tipos.size>1?'Todos':[...r.tipos][0];
    const tipoCor=r.tipos.size>1?'#64748b':(COR[tipoLabel]||'#64748b');
    return '<tr>'
    +'<td style="color:#475569">'+(i+1)+'</td>'
    +'<td>'+r.usina+'</td>'
    +'<td>'+r.conjunto+'</td>'
    +'<td><span class="fonte-tag ft-'+r.fonte+'">'+r.fonte+'</span></td>'
    +'<td>'+r.uf+'</td>'
    +'<td><span class="dot" style="background:'+tipoCor+'"></span>'+tipoLabel+'</td>'
    +'<td>'+fmt1(r.corte/H)+'</td>'
    +'</tr>';}).join('');
}

initFiltros();
render();
</script>
</body>
</html>
"""


# ─── Geração do HTML ──────────────────────────────────────────────────────────

def gerar_html(data_dict: dict, saida: Path, logo_tag: str):
    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = (HTML_TEMPLATE
            .replace("__DATA_JSON__", json.dumps(data_dict, ensure_ascii=False))
            .replace("__GERADO_EM__", gerado_em)
            .replace("__LOGO__",      logo_tag))
    saida.write_text(html, encoding="utf-8")
    print(f"\n✅ Dashboard salvo: {saida.resolve()}")
    print("   Abra o arquivo no navegador (duplo clique ou arraste para o Chrome/Safari).")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="C-OFF ONS → Dashboard HTML")
    parser.add_argument("--inicio",    default=None, help="Mês inicial YYYY-MM (ex: 2024-04)")
    parser.add_argument("--fim",       default=None, help="Mês final   YYYY-MM (ex: 2026-06)")
    parser.add_argument("--mes",       default=None, help="Mês único   YYYY-MM (ex: 2026-05)")
    parser.add_argument("--fonte",     default="AMBAS", choices=["UFV","EOL","AMBAS"])
    parser.add_argument("--so-local",  action="store_true",
                        help="Não tenta baixar — usa só arquivos já presentes")
    parser.add_argument("--saida",     default="dashboard_cortes.html")
    args = parser.parse_args()

    # Aponta DIR_LOCAL para a pasta onde o script está (onde estão os parquets)
    global DIR_LOCAL
    DIR_LOCAL = Path(__file__).parent

    hoje   = date.today()
    fontes = ["UFV","EOL"] if args.fonte=="AMBAS" else [args.fonte]

    if args.mes:
        a, m = map(int, args.mes.split("-"))
        lista_meses = [(a, m)]
    else:
        a0, m0 = map(int, (args.inicio or MES_INICIAL.strftime("%Y-%m")).split("-"))
        a1, m1 = map(int, (args.fim or date(hoje.year, hoje.month, 1).strftime("%Y-%m")).split("-"))
        lista_meses = list(meses_entre(date(a0,m0,1), date(a1,m1,1)))

    print(f"Processando {len(lista_meses)} mês(es) × {len(fontes)} fonte(s)...\n")

    manifest_path = DIR_LOCAL / "_manifest_ons.csv"
    manifest = carregar_manifest(manifest_path)

    cadastro_ponto_path = DIR_LOCAL / CADASTRO_PONTO_CONEXAO_CSV
    cadastro_ponto = carregar_cadastro_ponto_conexao(cadastro_ponto_path)

    resultado = {
        "meta": {
            "horas_por_mes":     {},
            "meses_disponiveis": [],
            "fontes_disponiveis":[],
            "gerado_em":         datetime.now().strftime("%d/%m/%Y %H:%M"),
        },
        "diario_tipo":     [],
        "mensal_conjunto": [],
        "mensal_estado":   [],
        "mensal_total":    [],
        "mensal_usinas":   [],
        "mensal_conjunto_geracao": [],
        "mensal_usinas_geracao":   [],
        "diario_geracao":          [],
    }

    meses_ok   = set()
    fontes_ok  = set()

    try:
        for ano, mes in lista_meses:
            label = f"{ano}-{mes:02d}"
            for fonte in fontes:
                print(f"── {label} {fonte} ──")
                r = processar_mes(ano, mes, fonte, args.so_local, manifest, cadastro_ponto)
                if r is None:
                    print()
                    continue
                resultado["meta"]["horas_por_mes"][label] = r["horas"]
                meses_ok.add(label)
                fontes_ok.add(fonte)
                resultado["diario_tipo"]     += r["diario"]
                resultado["mensal_conjunto"] += r["conj"]
                resultado["mensal_estado"]   += r["estado"]
                resultado["mensal_total"]    += r["total"]
                resultado["mensal_usinas"]   += r["usinas"]
                resultado["mensal_conjunto_geracao"] += r["conj_geracao"]
                resultado["mensal_usinas_geracao"]   += r["usinas_geracao"]
                resultado["diario_geracao"]          += r["diario_geracao"]
                print()
    finally:
        # Salva o manifest mesmo que algo falhe no meio do processamento,
        # para não perder o progresso de arquivos já verificados/baixados.
        if not args.so_local:
            salvar_manifest(manifest, manifest_path)
            print(f"Manifest de controle incremental atualizado: {manifest_path}")
            salvar_cadastro_ponto_conexao(cadastro_ponto, cadastro_ponto_path)
            print(f"Cadastro de ponto de conexão atualizado: {cadastro_ponto_path}\n")

    resultado["meta"]["meses_disponiveis"] = sorted(meses_ok)
    resultado["meta"]["fontes_disponiveis"] = sorted(fontes_ok)

    if not meses_ok:
        print("Nenhum mês processado com sucesso.")
        sys.exit(1)

    print("Carregando logo...")
    logo_tag = carregar_logo()

    saida = Path(args.saida)
    gerar_html(resultado, saida, logo_tag)
    print(f"\nMeses processados: {', '.join(sorted(meses_ok))}")
    print(f"Fontes:            {', '.join(sorted(fontes_ok))}")


if __name__ == "__main__":
    main()
