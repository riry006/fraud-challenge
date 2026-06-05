"""
Interface Streamlit — Hackathon INTELO 2026
FraudGuard · Détection de fraude financière
Direction : editorial / presse financière — sobre, lisible, percutant
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from fraud_detection import detect_fraud, load_transactions

SAMPLE_CSV = Path(__file__).parent / "data" / "sample_transactions.csv"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap');

:root {
    --ink:     #1a1814;
    --stone:   #6b6660;
    --rule:    #d4cfc9;
    --paper:   #f7f4f0;
    --cream:   #ede9e3;
    --alert:   #c0392b;
    --alert-bg:#fdf0ee;
    --safe:    #1a6644;
    --safe-bg: #eef6f1;
    --mono:    'IBM Plex Mono', monospace;
    --serif:   'Source Serif 4', Georgia, serif;
    --display: 'Playfair Display', Georgia, serif;
}

html, body, [class*="css"] {
    font-family: var(--serif);
    color: var(--ink);
}

.stApp { background: var(--paper); }

[data-testid="stSidebar"] {
    background: var(--cream) !important;
    border-right: 1px solid var(--rule) !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Masthead */
.masthead {
    border-top: 3px solid var(--ink);
    border-bottom: 1px solid var(--rule);
    padding: 18px 0 14px;
    margin-bottom: 28px;
    display: flex;
    align-items: baseline;
    gap: 20px;
}
.masthead-title {
    font-family: var(--display);
    font-weight: 900;
    font-size: 2.1rem;
    letter-spacing: -1px;
    line-height: 1;
    color: var(--ink);
}
.masthead-sub {
    font-family: var(--mono);
    font-size: .65rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--stone);
    padding-top: 2px;
}
.masthead-date {
    font-family: var(--mono);
    font-size: .65rem;
    color: var(--stone);
    margin-left: auto;
}

/* Section label */
.section-label {
    font-family: var(--mono);
    font-size: .6rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--stone);
    border-top: 1px solid var(--rule);
    padding-top: 10px;
    margin-bottom: 14px;
}

/* Stat strip */
.stat-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border: 1px solid var(--rule);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 28px;
}
.stat-cell {
    padding: 16px 20px;
    border-right: 1px solid var(--rule);
}
.stat-cell:last-child { border-right: none; }
.stat-label {
    font-family: var(--mono);
    font-size: .58rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--stone);
    margin-bottom: 6px;
}
.stat-value {
    font-family: var(--display);
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1;
    color: var(--ink);
}
.stat-value.red   { color: var(--alert); }
.stat-value.green { color: var(--safe);  }

/* Transaction row */
.tx-row {
    display: grid;
    grid-template-columns: 100px 80px 1fr 90px 130px 80px 120px;
    gap: 0;
    border-bottom: 1px solid var(--rule);
    padding: 11px 0;
    align-items: center;
    font-family: var(--mono);
    font-size: .75rem;
    color: var(--ink);
}
.tx-row.header {
    font-size: .58rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--stone);
    padding: 8px 0;
    border-bottom: 2px solid var(--ink);
}
.tx-row.flagged { background: var(--alert-bg); margin: 0 -12px; padding: 11px 12px; }
.tx-cell { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tx-cell.right { text-align: right; }
.tx-cell.amount { font-weight: 500; }
.tx-cell.merchant { font-family: var(--serif); font-size: .82rem; }

/* Risk pill */
.pill {
    display: inline-block;
    font-family: var(--mono);
    font-size: .6rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 2px;
}
.pill.alert { background: var(--alert-bg); color: var(--alert); border: 1px solid #e5bab6; }
.pill.safe  { background: var(--safe-bg);  color: var(--safe);  border: 1px solid #b0d4c0; }

/* Score bar inline */
.score-inline {
    display: flex; align-items: center; gap: 6px;
}
.score-track {
    width: 52px; height: 3px;
    background: var(--rule); border-radius: 2px; overflow: hidden;
}
.score-fill { height: 100%; border-radius: 2px; }
.score-txt { font-family: var(--mono); font-size: .65rem; color: var(--stone); }

/* Timeline */
.tl-wrap { padding-left: 0; }
.tl-entry {
    display: grid;
    grid-template-columns: 140px 16px 1fr;
    gap: 0 16px;
    margin-bottom: 0;
}
.tl-ts {
    font-family: var(--mono);
    font-size: .68rem;
    color: var(--stone);
    text-align: right;
    padding-top: 14px;
    line-height: 1.4;
}
.tl-spine {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.tl-dot-outer {
    width: 14px; height: 14px; border-radius: 50%;
    border: 2px solid var(--rule);
    background: var(--paper);
    display: flex; align-items: center; justify-content: center;
    margin-top: 14px; flex-shrink: 0; position: relative; z-index: 1;
}
.tl-dot-inner { width: 6px; height: 6px; border-radius: 50%; background: var(--rule); }
.tl-dot-outer.flagged { border-color: var(--alert); }
.tl-dot-outer.flagged .tl-dot-inner { background: var(--alert); }
.tl-line { flex: 1; width: 1px; background: var(--rule); }
.tl-card {
    border: 1px solid var(--rule);
    border-radius: 2px;
    padding: 12px 16px;
    margin: 8px 0 8px;
    background: white;
}
.tl-card.flagged { border-color: #e5bab6; border-left: 3px solid var(--alert); background: var(--alert-bg); }
.tl-card-top { display: flex; justify-content: space-between; align-items: baseline; }
.tl-merchant { font-family: var(--display); font-size: 1rem; font-weight: 700; }
.tl-amount   { font-family: var(--mono); font-size: .8rem; }
.tl-country  { font-family: var(--mono); font-size: .65rem; color: var(--stone); margin-top: 2px; }
.tl-reason   {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #e5bab6;
    font-family: var(--serif);
    font-style: italic;
    font-size: .8rem;
    color: var(--alert);
    line-height: 1.5;
}

/* Alert detail */
.alert-headline {
    font-family: var(--display);
    font-weight: 900;
    font-size: 1.6rem;
    line-height: 1.2;
    color: var(--alert);
    border-left: 4px solid var(--alert);
    padding-left: 14px;
    margin-bottom: 20px;
}
.alert-score-large {
    font-family: var(--display);
    font-size: 5rem;
    font-weight: 900;
    color: var(--alert);
    line-height: 1;
}
.alert-score-label {
    font-family: var(--mono);
    font-size: .6rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--stone);
}

.fact-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 16px 0;
}
.fact-item { border-top: 1px solid var(--rule); padding-top: 8px; }
.fact-label { font-family: var(--mono); font-size: .6rem; letter-spacing: 1.5px;
              text-transform: uppercase; color: var(--stone); margin-bottom: 3px; }
.fact-value { font-family: var(--mono); font-size: .82rem; color: var(--ink); }

.rule-block {
    border-top: 1px solid var(--rule);
    padding: 14px 0;
}
.rule-block:first-child { border-top: 2px solid var(--ink); }
.rule-name {
    font-family: var(--mono);
    font-size: .65rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--alert);
    margin-bottom: 5px;
}
.rule-text {
    font-family: var(--serif);
    font-size: .88rem;
    color: var(--ink);
    line-height: 1.55;
}
.rule-evidence {
    margin-top: 6px;
    font-family: var(--mono);
    font-size: .72rem;
    color: var(--stone);
}

.verdict-bar {
    border-top: 2px solid var(--ink);
    padding-top: 14px;
    margin-top: 20px;
    display: flex;
    align-items: baseline;
    gap: 12px;
}
.verdict-label { font-family: var(--mono); font-size: .6rem; letter-spacing: 2px;
                 text-transform: uppercase; color: var(--stone); }
.verdict-text  { font-family: var(--serif); font-style: italic; font-size: .9rem; color: var(--ink); }

/* Sidebar */
.sb-title {
    font-family: var(--display);
    font-size: 1.1rem;
    font-weight: 700;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 6px;
    margin-bottom: 10px;
}
.sb-note {
    font-family: var(--mono);
    font-size: .62rem;
    color: var(--stone);
    line-height: 1.7;
}

/* Streamlit overrides */
.stButton > button {
    background: var(--ink) !important;
    color: var(--paper) !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: var(--mono) !important;
    font-size: .72rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: .55rem 1.8rem !important;
}
.stButton > button:hover { background: var(--alert) !important; }
[data-baseweb="tab"] { font-family: var(--mono) !important; font-size: .65rem !important;
                        letter-spacing: 1.5px !important; text-transform: uppercase !important; }
.stSelectbox label, .stRadio label { font-family: var(--mono) !important;
                                      font-size: .65rem !important; color: var(--stone) !important; }
hr { border-color: var(--rule) !important; }
.stCaption { font-family: var(--mono) !important; font-size: .62rem !important;
             color: var(--stone) !important; }
</style>
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_ts(ts, short=False):
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y" if short else "%d %b %Y\n%H:%M UTC")
    except Exception:
        return str(ts)


def _fmt_amount(row):
    try:
        return f"{float(row.get('amount')):,.2f} {row.get('currency','') or ''}"
    except Exception:
        return "—"


def _score_bar_html(score):
    pct = int(score * 100)
    color = "var(--alert)" if score >= 0.7 else ("#d4a020" if score >= 0.4 else "var(--safe)")
    return (f'<div class="score-inline">'
            f'<div class="score-track"><div class="score-fill" style="width:{pct}%;background:{color}"></div></div>'
            f'<span class="score-txt">{pct}%</span></div>')


def _pill(suspicious):
    if suspicious:
        return '<span class="pill alert">Alerte</span>'
    return '<span class="pill safe">Conforme</span>'


# ── Sections ─────────────────────────────────────────────────────────────────

def _render_stats(df):
    n_total = len(df)
    n_alert = int(df["is_suspicious"].sum())
    n_safe  = n_total - n_alert
    avg     = float(df["fraud_score"].mean())

    st.markdown(f"""
    <div class="stat-strip">
      <div class="stat-cell">
        <div class="stat-label">Transactions</div>
        <div class="stat-value">{n_total}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-label">Alertes</div>
        <div class="stat-value red">{n_alert}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-label">Conformes</div>
        <div class="stat-value green">{n_safe}</div>
      </div>
      <div class="stat-cell">
        <div class="stat-label">Score moyen</div>
        <div class="stat-value">{avg:.0%}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def _render_table(df):
    header = """
    <div class="tx-row header">
      <div class="tx-cell">ID</div>
      <div class="tx-cell">Client</div>
      <div class="tx-cell merchant">Marchand</div>
      <div class="tx-cell right">Montant</div>
      <div class="tx-cell">Pays · Devise</div>
      <div class="tx-cell">Score</div>
      <div class="tx-cell">Statut</div>
    </div>"""
    rows = ""
    for _, r in df.iterrows():
        sus = bool(r["is_suspicious"])
        cls = "flagged" if sus else ""
        country = r.get("country") or "—"
        currency = r.get("currency") or "—"
        rows += f"""
        <div class="tx-row {cls}">
          <div class="tx-cell" style="font-family:var(--mono);font-size:.68rem;color:var(--stone)">{r['transaction_id']}</div>
          <div class="tx-cell" style="font-family:var(--mono);font-size:.72rem">{r.get('user_id','—')}</div>
          <div class="tx-cell merchant">{r.get('merchant','—')}</div>
          <div class="tx-cell right amount">{_fmt_amount(r)}</div>
          <div class="tx-cell" style="font-family:var(--mono);font-size:.7rem">{country} · {currency}</div>
          <div class="tx-cell">{_score_bar_html(float(r['fraud_score']))}</div>
          <div class="tx-cell">{_pill(sus)}</div>
        </div>"""
    st.markdown(header + rows, unsafe_allow_html=True)


def _render_timeline(df, uid):
    udf = df[df["user_id"] == uid].copy()
    udf = udf.sort_values("timestamp", na_position="last")

    for i, (_, r) in enumerate(udf.iterrows()):
        sus = bool(r["is_suspicious"])
        score = float(r["fraud_score"])
        ts = _fmt_ts(r.get("timestamp"), short=True)
        merchant = r.get("merchant") or "—"
        amount = _fmt_amount(r)
        country = r.get("country") or "—"
        tid = r.get("transaction_id") or "—"
        reason = r.get("reason") or ""

        col_ts, col_card = st.columns([1, 4])

        with col_ts:
            st.markdown(
                f"<div style='text-align:right;font-family:var(--mono);font-size:.68rem;"
                f"color:var(--stone);padding-top:16px;line-height:1.5'>{ts}</div>",
                unsafe_allow_html=True)

        with col_card:
            border_color = "var(--alert)" if sus else "var(--rule)"
            bg_color = "var(--alert-bg)" if sus else "white"
            border_left = f"3px solid {border_color}" if sus else f"1px solid {border_color}"
            dot = "🔴" if sus else "⚪"

            header_html = (
                f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                f"<span style='font-family:var(--display);font-weight:700;font-size:1rem'>{dot} {merchant}</span>"
                f"<span style='font-family:var(--mono);font-size:.8rem'>{amount}</span>"
                f"</div>"
                f"<div style='font-family:var(--mono);font-size:.65rem;color:var(--stone);margin-top:3px'>"
                f"{country} · {tid} · {_score_bar_html(score)}</div>"
            )
            reason_html = ""
            if sus and reason:
                reason_html = (
                    f"<div style='margin-top:10px;padding-top:10px;border-top:1px solid #e5bab6;"
                    f"font-family:var(--serif);font-style:italic;font-size:.8rem;"
                    f"color:var(--alert);line-height:1.5'>⚑ {reason}</div>"
                )

            st.markdown(
                f"<div style='border:{border_left};border-radius:2px;padding:12px 16px;"
                f"background:{bg_color};margin-bottom:8px'>"
                f"{header_html}{reason_html}</div>",
                unsafe_allow_html=True)


def _render_alert_detail(row, df):
    tid   = row["transaction_id"]
    uid   = row.get("user_id", "—")
    score = float(row["fraud_score"])
    reason = str(row.get("reason", "—"))

    st.markdown(
        f'<div class="alert-headline">Transaction {tid} signalée comme suspecte</div>',
        unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown(
            f'<div class="alert-score-large">{score:.0%}</div>'
            f'<div class="alert-score-label">Score de risque</div>',
            unsafe_allow_html=True)

        facts = {
            "Client":      uid,
            "Horodatage":  _fmt_ts(row.get("timestamp"), short=True),
            "Montant":     _fmt_amount(row),
            "Pays":        row.get("country") or "—",
            "Marchand":    row.get("merchant") or "—",
            "Carte phys.": "Oui" if row.get("card_present") else "Non",
        }
        facts_html = '<div class="fact-grid">'
        for k, v in facts.items():
            facts_html += (f'<div class="fact-item">'
                           f'<div class="fact-label">{k}</div>'
                           f'<div class="fact-value">{v}</div></div>')
        facts_html += "</div>"
        st.markdown(facts_html, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-label">Analyse des signaux</div>', unsafe_allow_html=True)

        # Rule descriptions
        RULE_MAP = {
            "montant nul ou négatif": (
                "Montant invalide",
                "Un montant nul ou négatif ne correspond à aucune transaction commerciale standard. "
                "Ce type de valeur peut indiquer une erreur de traitement ou une tentative de manipulation.",
                None,
            ),
            "champs obligatoires manquants": (
                "Données incomplètes",
                "Des champs essentiels à l'identification de la transaction sont absents. "
                "L'absence de pays ou de devise rend impossible la validation géographique et réglementaire.",
                None,
            ),
            "montant très supérieur": (
                "Montant hors profil",
                "Le montant de cette transaction dépasse significativement le comportement habituel du client. "
                "Une telle rupture de profil est un signal classique de compromission de compte.",
                _evidence_amount(df, uid, row),
            ),
            "deux pays différents": (
                "Incohérence géographique",
                "Deux transactions ont été effectuées dans des pays séparés par une distance impossible à "
                "parcourir dans le délai observé. Ce pattern est caractéristique d'une fraude à la carte.",
                _evidence_geo(df, uid, row),
            ),
            "fréquence de transactions": (
                "Rafale suspecte",
                "Un nombre anormalement élevé de transactions a été enregistré en très peu de temps. "
                "Ce comportement correspond à un test de validité de carte volée.",
                None,
            ),
        }

        triggered = [r.strip() for r in reason.split(";") if r.strip()]
        rules_html = ""
        for rule_text in triggered:
            title, desc, evidence = rule_text, rule_text, None
            for key, (t, d, e) in RULE_MAP.items():
                if key in rule_text.lower():
                    title, desc, evidence = t, d, e
                    break
            ev_html = f'<div class="rule-evidence">↳ {evidence}</div>' if evidence else ""
            rules_html += (f'<div class="rule-block">'
                           f'<div class="rule-name">{title}</div>'
                           f'<div class="rule-text">{desc}</div>'
                           f'{ev_html}</div>')

        # Verdict
        if score >= 0.85:
            verdict = "Bloquer la transaction et contacter le titulaire immédiatement."
        elif score >= 0.6:
            verdict = "Soumettre à vérification manuelle avant exécution."
        else:
            verdict = "Surveiller sans intervention immédiate."

        st.markdown(
            rules_html +
            f'<div class="verdict-bar">'
            f'<span class="verdict-label">Recommandation</span>'
            f'<span class="verdict-text">{verdict}</span>'
            f'</div>',
            unsafe_allow_html=True)


def _evidence_amount(df, uid, row):
    try:
        udf = df[(df["user_id"] == uid) & (df["amount"].notna()) & (df["amount"] > 0)]
        if len(udf) < 2:
            return None
        avg = udf["amount"].mean()
        val = float(row.get("amount", 0))
        return f"Moyenne client : {avg:,.2f} — cette transaction est {val/avg:.1f}× supérieure"
    except Exception:
        return None


def _evidence_geo(df, uid, row):
    try:
        country = row.get("country")
        if not country:
            return None
        udf = df[(df["user_id"] == uid) & (df["country"].notna()) & (df["country"] != country)]
        if udf.empty:
            return None
        others = ", ".join(udf["country"].unique())
        return f"Pays de cette transaction : {country} — autres pays détectés : {others}"
    except Exception:
        return None


# ── render_interface ──────────────────────────────────────────────────────────

def render_interface(transactions: list[dict], results: list[dict]) -> None:
    tx_map = {t["transaction_id"]: t for t in transactions}
    rows   = [{**tx_map.get(r["transaction_id"], {}), **r} for r in results]
    df     = pd.DataFrame(rows)

    _render_stats(df)

    tab1, tab2, tab3 = st.tabs(["Transactions", "Timeline client", "Détail alerte"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            filtre = st.radio("", ["Toutes", "Alertes", "Conformes"], horizontal=True)
        with c2:
            users = ["Tous les clients"] + sorted(df["user_id"].dropna().unique().tolist())
            user_sel = st.selectbox("", users, key="t1u")
        with c3:
            pays = ["Tous pays"] + sorted(df["country"].dropna().unique().tolist())
            pays_sel = st.selectbox("", pays, key="t1p")

        view = df.copy()
        if filtre == "Alertes":   view = view[view["is_suspicious"]]
        if filtre == "Conformes": view = view[~view["is_suspicious"]]
        if user_sel != "Tous les clients": view = view[view["user_id"] == user_sel]
        if pays_sel != "Tous pays":        view = view[view["country"] == pays_sel]

        st.caption(f"{len(view)} résultat(s)")
        st.markdown("<br>", unsafe_allow_html=True)
        _render_table(view)

    with tab2:
        users_list = sorted(df["user_id"].dropna().unique().tolist())
        if not users_list:
            st.info("Aucun client trouvé.")
        else:
            uid = st.selectbox("Client", users_list, key="t2u")
            st.markdown("<br>", unsafe_allow_html=True)
            _render_timeline(df, uid)

    with tab3:
        sus_ids = df[df["is_suspicious"]]["transaction_id"].tolist()
        if not sus_ids:
            st.markdown(
                '<div style="font-family:var(--serif);font-style:italic;color:var(--safe);padding:20px 0">'
                'Aucune alerte dans ce lot de transactions.</div>',
                unsafe_allow_html=True)
        else:
            sel = st.selectbox("Transaction suspecte", sus_ids, key="t3s")
            st.markdown("<br>", unsafe_allow_html=True)
            row = df[df["transaction_id"] == sel].iloc[0]
            _render_alert_detail(row, df)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="FraudGuard · INTELO 2026",
        page_icon="⚑",
        layout="wide",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sb-title">FraudGuard</div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-note">Hackathon INTELO 2026<br>Détection de fraude financière</div>',
                    unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        use_sample = st.toggle("Données d'exemple", value=True)
        transactions: list[dict] = []

        if use_sample:
            transactions = load_transactions(str(SAMPLE_CSV))
            st.caption(f"{len(transactions)} transactions chargées")
        else:
            uploaded = st.file_uploader("Importer un CSV", type=["csv"])
            if uploaded:
                tmp = Path(".upload_tmp.csv")
                tmp.write_bytes(uploaded.getvalue())
                transactions = load_transactions(str(tmp))
                tmp.unlink(missing_ok=True)
                st.caption(f"{len(transactions)} transactions importées")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""<div class="sb-note">
        Signaux analysés :<br>
        · Montant hors historique<br>
        · Voyage géographiquement impossible<br>
        · Fréquence anormale<br>
        · Champs manquants<br>
        · Montant nul ou négatif
        </div>""", unsafe_allow_html=True)

    today = datetime.now().strftime("%d %B %Y").upper()
    st.markdown(f"""
    <div class="masthead">
      <div class="masthead-title">FraudGuard</div>
      <div class="masthead-sub">Analyse des transactions · INTELO 2026</div>
      <div class="masthead-date">{today}</div>
    </div>""", unsafe_allow_html=True)

    if not transactions:
        st.markdown('<div style="font-family:var(--serif);font-style:italic;color:var(--stone);padding:40px 0">'
                    'Chargez un fichier depuis la barre latérale pour démarrer.</div>',
                    unsafe_allow_html=True)
        return

    if st.button("Analyser", type="primary"):
        with st.spinner(""):
            try:
                results = detect_fraud(transactions)
            except NotImplementedError:
                st.error("Implémentez d'abord detect_fraud dans fraud_detection.py")
                return
            except Exception as e:
                st.error(f"Erreur : {e}")
                return
        st.session_state["results"]      = results
        st.session_state["transactions"] = transactions

    if "results" in st.session_state:
        render_interface(st.session_state["transactions"], st.session_state["results"])


if __name__ == "__main__":
    main()