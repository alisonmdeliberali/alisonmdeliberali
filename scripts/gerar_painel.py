#!/usr/bin/env python3
"""
Gera o painel.svg: um "diagnóstico" bem-humorado do seu perfil no GitHub.
Só usa a biblioteca padrão do Python. Variáveis de ambiente:
  GH_USER   -> seu usuário (no Actions vem automático do dono do repositório)
  GH_TOKEN  -> token (no Actions, o GITHUB_TOKEN já basta)
  FUSO      -> fuso horário para o relógio biológico (padrão America/Sao_Paulo)
"""
import json, os, random, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cidade import desenhar_cidade, ALTURA as ALTURA_CIDADE
from collections import Counter
from datetime import datetime, date, timezone
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

USER = os.environ.get("GH_USER", "").strip()
TOKEN = os.environ.get("GH_TOKEN", "").strip()
FUSO = ZoneInfo(os.environ.get("FUSO", "America/Sao_Paulo"))
SAIDA = os.environ.get("SAIDA", "painel.svg")
API = "https://api.github.com"


def req(url, data=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "painel-dev"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    body = json.dumps(data).encode() if data else None
    with urllib.request.urlopen(urllib.request.Request(url, body, h), timeout=30) as r:
        return json.loads(r.read())


def paginar(url):
    itens, pagina = [], 1
    while True:
        lote = req(f"{url}{'&' if '?' in url else '?'}per_page=100&page={pagina}")
        itens += lote
        if len(lote) < 100 or pagina >= 10:
            return itens
        pagina += 1


# ---------- coleta ----------
perfil = req(f"{API}/users/{USER}")
repos = [r for r in paginar(f"{API}/users/{USER}/repos?type=owner") if not r["fork"]]
estrelas = sum(r["stargazers_count"] for r in repos)
xodo = max(repos, key=lambda r: r["stargazers_count"], default=None)

linguagens = Counter()
for r in repos[:60]:  # limite gentil com a API
    try:
        linguagens.update(req(r["languages_url"]))
    except Exception:
        pass
total_bytes = sum(linguagens.values()) or 1
top_ling = [(l, b / total_bytes) for l, b in linguagens.most_common(5)]

horas = Counter()
try:
    for ev in paginar(f"{API}/users/{USER}/events/public"):
        if ev["type"] in ("PushEvent", "PullRequestEvent", "IssuesEvent", "CreateEvent"):
            quando = datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
            horas[quando.astimezone(FUSO).hour] += 1
except Exception:
    pass

commits_ano, seq_atual, seq_max, dia_fav = None, 0, 0, None
semanas = []  # (data de início, contribuições) das últimas semanas
if TOKEN:
    try:
        q = """query($u:String!){user(login:$u){contributionsCollection{
              totalCommitContributions contributionCalendar{weeks{contributionDays{
              date contributionCount weekday}}}}}}"""
        cc = req(f"{API}/graphql", {"query": q, "variables": {"u": USER}})["data"]["user"]["contributionsCollection"]
        commits_ano = cc["totalCommitContributions"]
        semanas_api = cc["contributionCalendar"]["weeks"]
        semanas = [(w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
                   for w in semanas_api][-16:]
        dias = [d for w in semanas_api for d in w["contributionDays"]]
        corrida = 0
        for d in dias:
            corrida = corrida + 1 if d["contributionCount"] else 0
            seq_max = max(seq_max, corrida)
        hoje = date.today().isoformat()
        for d in reversed(dias):
            if d["date"] == hoje and not d["contributionCount"]:
                continue  # hoje ainda tem tempo, não quebra a sequência
            if not d["contributionCount"]:
                break
            seq_atual += 1
        por_dia = Counter()
        for d in dias:
            por_dia[d["weekday"]] += d["contributionCount"]
        if sum(por_dia.values()):
            dia_fav = por_dia.most_common(1)[0][0]
    except Exception as e:
        print("GraphQL indisponível, seguindo sem sequências:", e)

# ---------- a parte divertida ----------
anos = (datetime.now(timezone.utc) - datetime.fromisoformat(perfil["created_at"].replace("Z", "+00:00"))).days // 365
hora_pico = horas.most_common(1)[0][0] if horas else None

if hora_pico is None:
    persona = ("🕵️", "Dev misterioso", "Atividade pública discreta. Ninguém sabe quando você coda.")
elif 5 <= hora_pico < 12:
    persona = ("☀️", "Madrugador produtivo", f"Pico às {hora_pico}h. Commita antes do café esfriar.")
elif 12 <= hora_pico < 18:
    persona = ("🌤️", "Dev de expediente", f"Pico às {hora_pico}h. Equilíbrio raro, quase lendário.")
elif 18 <= hora_pico < 24:
    persona = ("🌙", "Coruja do código", f"Pico às {hora_pico}h. O melhor código nasce depois da janta.")
else:
    persona = ("🦇", "Vampiro do deploy", f"Pico às {hora_pico}h. Dormir é opcional, o merge não.")

PIADAS_LING = {
    "Python": "Indentação é estilo de vida.",
    "JavaScript": "undefined is not a function, e tudo bem.",
    "TypeScript": "Tipou até a lista de compras.",
    "Java": "Fábrica de fábricas de fábricas.",
    "PHP": "Sobreviveu a todos os obituários.",
    "C#": "Ponto e vírgula com orgulho.",
    "Go": "if err != nil { return err } x 1000",
    "Rust": "Brigou com o borrow checker e venceu.",
    "C": "Gerencia memória na unha.",
    "C++": "Compila enquanto você toma café. E almoça.",
    "HTML": "Sim, é linguagem. Pelo menos aqui.",
    "CSS": "Centralizou uma div na primeira tentativa.",
    "Ruby": "Feliz por padrão.",
    "Kotlin": "Java, mas com bom humor.",
    "Swift": "Rápido no nome e na prática.",
    "Dart": "Um widget dentro de outro widget.",
    "Shell": "Automatiza até o próprio café.",
    "Jupyter Notebook": "Célula 47 rodada antes da célula 3.",
    "Vue": "Reatividade com elegância.",
}
top_nome = top_ling[0][0] if top_ling else None
piada_ling = PIADAS_LING.get(top_nome, "Escolha de quem sabe o que faz.") if top_nome else "Ainda escolhendo a linguagem favorita."

def frase_seq(n):
    if n == 0: return "Hoje é um ótimo dia para recomeçar."
    if n < 7: return "Aquecendo os motores."
    if n < 30: return "O hábito já está criando raízes."
    return "Isso aí já é estilo de vida."

def frase_estrelas(n):
    if n == 0: return "O céu está limpo. Por enquanto."
    if n < 10: return "Primeiras estrelas no céu."
    if n < 100: return "Já dá pra montar uma constelação."
    return "Praticamente uma galáxia."

DIAS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"]
FRASE_DIA = {0: "Code no domingo? Respeito.", 1: "Começa a semana com tudo.", 5: "Deploy na sexta. Corajoso.", 6: "Sábado é dia de projeto pessoal."}

linhas = []
if commits_ano is not None:
    linhas.append(("Commits este ano", f"{commits_ano:,}".replace(",", "."), f"≈ {commits_ano // 2} cafés consumidos (ciência duvidosa)."))
    linhas.append(("Sequência atual", f"{seq_atual} dias", f"{frase_seq(seq_atual)} Recorde: {seq_max}."))
linhas.append(("Estrelas recebidas", str(estrelas), frase_estrelas(estrelas)))
if xodo and xodo["stargazers_count"]:
    linhas.append(("Repositório xodó", xodo["name"][:22], f"{xodo['stargazers_count']} estrelas. O queridinho da casa."))
else:
    linhas.append(("Repositórios", str(len(repos)), "Cada um com sua história."))
linhas.append(("Tempo de GitHub", f"{anos} anos" if anos != 1 else "1 ano", "Veterano de guerra." if anos >= 5 else "A jornada só começou."))
if dia_fav is not None:
    linhas.append(("Dia favorito", DIAS[dia_fav], FRASE_DIA.get(dia_fav, "Produtividade no meio da semana.")))

# ---------- desenho ----------
W = 840
DESLOC = ALTURA_CIDADE + 20  # espaço da cidade animada
base = 396  # topo do cartão de linguagens
H = DESLOC + base + 72 + max(len(top_ling), 1) * 24 + 20
CORES = ["#2F6FEB", "#2FBF9B", "#F2B33D", "#E5534B", "#8B6FE8"]
s = []
add = s.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Diagnóstico do perfil de {escape(USER)}">')
add("""<style>
  :root{--fundo:#F3F6FD;--cartao:#FFFFFF;--tinta:#1B2440;--suave:#5C6888;--linha:#DCE3F2;--trilho:#E8EDF8}
  @media (prefers-color-scheme: dark){:root{--fundo:#0F1730;--cartao:#172142;--tinta:#E6ECFA;--suave:#9AA7C7;--linha:#26335C;--trilho:#22305A}}
  text{font-family:'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif;fill:var(--tinta)}
  .suave{fill:var(--suave)} .t{font-size:13px} .p{font-size:12px}
  .valor{font-size:20px;font-weight:700} .rotulo{font-size:12px;fill:var(--suave)}
  :root{--ceu:#DCE8FF;--chao:#C3D1EE;--faixa:#FFFFFF;--astro:#FFC94D;--estrelas:0;--predio:#A9BCE4;--lado:#8599C7;--teto:#C7D5F1;--janela:#FFE08A;--janela-off:#8DA0CC}
  @media (prefers-color-scheme: dark){:root{--ceu:#0A1330;--chao:#131D3B;--faixa:#2A3866;--astro:#E9EEF9;--estrelas:1;--predio:#22305C;--lado:#18234A;--teto:#30427A;--janela:#FFD66B;--janela-off:#1A2650}}
  .titulo{font-size:24px;font-weight:700} .persona{font-size:19px;font-weight:700}
  .barra{animation:cresce 1.2s ease-out both;transform-box:fill-box;transform-origin:left}
  @keyframes cresce{from{transform:scaleX(0)}}
  @media (prefers-reduced-motion: reduce){*{animation:none!important}}
</style>""")
add(f'<rect width="{W}" height="{H}" rx="16" style="fill:var(--fundo)"/>')
nome = escape(perfil.get("name") or USER)
add(f'<text x="32" y="50" class="titulo">Diagnóstico de {nome}</text>')
agora = datetime.now(FUSO).strftime("%d/%m/%Y às %Hh%M")
add(f'<text x="32" y="74" class="p suave">Laudo emitido em {agora} por um robô que não toma café</text>')

# cidade animada: cada prédio é uma semana, construída pelos agentes
if semanas:
    valores = [v for _, v in semanas]
    d0 = semanas[0][0]
    legenda = f"Cada prédio é uma semana de contribuições desde {d0[8:10]}/{d0[5:7]}. O azul ainda está em obra."
    semana_atual = valores[-1]
else:
    escolhidos = sorted(repos, key=lambda r: r.get("pushed_at") or "")[-16:]
    valores = [r["stargazers_count"] * 5 + len(str(r.get("size", 0))) * 3 for r in escolhidos] or [1]
    legenda = "Cada prédio é um repositório. O azul é o mais recente, ainda em obra."
    semana_atual = len(repos)
mensagens = [
    f"feat: +{semana_atual} andares nesta semana",
    f"fix: janela do {top_nome or 'código'} que não acendia",
    "chore: reabastecer o café dos agentes",
    f"ci: prédio de @{USER} passou nos testes",
]
svg_cidade, css_cidade = desenhar_cidade(W - 64, valores, legenda, mensagens, USER)
add(f"<style>{css_cidade}</style>")
add(f'<g transform="translate(32,96)">{svg_cidade}</g>')
add(f'<g transform="translate(0,{DESLOC})">')

# cartão da persona
add(f'<rect x="32" y="96" width="300" height="280" rx="12" style="fill:var(--cartao);stroke:var(--linha)"/>')
add(f'<text x="52" y="150" style="font-size:40px">{persona[0]}</text>')
add(f'<text x="52" y="188" class="persona">{escape(persona[1])}</text>')
desc = persona[2]
partes = [desc]
if len(desc) > 40:
    corte = desc.rfind(" ", 0, 40)
    partes = [desc[:corte], desc[corte + 1:]]
for i, p in enumerate(partes):
    add(f'<text x="52" y="{212 + i * 17}" class="p suave">{escape(p)}</text>')
# prescrição médica (totalmente não científica)
RECEITAS = {
    "Madrugador produtivo": ["Manter o ritmo e", "não marcar reunião às 7h."],
    "Dev de expediente": ["Continuar assim e", "ensinar o segredo aos colegas."],
    "Coruja do código": ["Dormir antes das 2h.", "(Provavelmente será ignorada.)"],
    "Vampiro do deploy": ["Ver a luz do sol", "pelo menos uma vez por semana."],
    "Dev misterioso": ["Fazer um commit público", "para o robô te conhecer."],
}
add('<text x="52" y="262" class="rotulo">Prescrição</text>')
for i, linha in enumerate(RECEITAS[persona[1]]):
    add(f'<text x="52" y="{282 + i * 17}" class="p">{escape(linha)}</text>')
# relógio biológico: 24 barrinhas
add('<text x="52" y="330" class="rotulo">Relógio biológico (0h → 23h)</text>')
mx = max(horas.values()) if horas else 1
for h in range(24):
    alt = 2 + 16 * horas.get(h, 0) / mx
    cor = CORES[0] if h == hora_pico else "var(--suave)"
    op = "1" if h == hora_pico else "0.45"
    add(f'<rect x="{52 + h * 11}" y="{358 - alt:.1f}" width="8" height="{alt:.1f}" rx="2" style="fill:{cor};opacity:{op}"/>')

# coluna de estatísticas
y = 112
for rot, val, frase in linhas[:6]:
    add(f'<text x="360" y="{y}" class="rotulo">{escape(rot)}</text>')
    add(f'<text x="360" y="{y + 24}" class="valor">{escape(val)}</text>')
    add(f'<text x="520" y="{y + 22}" class="p suave">{escape(frase[:50])}</text>')
    y += 46 if len(linhas) > 5 else 54

# linguagens
add(f'<rect x="32" y="{base}" width="{W - 64}" height="{H - DESLOC - base - 24}" rx="12" style="fill:var(--cartao);stroke:var(--linha)"/>')
add(f'<text x="52" y="{base + 32}" class="t" style="font-weight:700">Linguagens mais usadas</text>')
add(f'<text x="{W - 52}" y="{base + 32}" class="p suave" text-anchor="end">{escape(top_nome or "")}{": " if top_nome else ""}{escape(piada_ling)}</text>')
largura = W - 104 - 190
for i, (ling, frac) in enumerate(top_ling):
    yy = base + 58 + i * 24
    add(f'<text x="52" y="{yy + 9}" class="p">{escape(ling[:18])}</text>')
    add(f'<rect x="190" y="{yy}" width="{largura}" height="10" rx="5" style="fill:var(--trilho)"/>')
    add(f'<rect class="barra" style="fill:{CORES[i]};animation-delay:{i * 0.12:.2f}s" x="190" y="{yy}" width="{max(largura * frac, 6):.1f}" height="10" rx="5"/>')
    add(f'<text x="{W - 52}" y="{yy + 9}" class="p suave" text-anchor="end">{frac * 100:.1f}%</text>')
if not top_ling:
    add(f'<text x="52" y="{base + 70}" class="p suave">Nenhum repositório público ainda. Crie o primeiro e o painel ganha cor.</text>')

add("</g>")
add("</svg>")
with open(SAIDA, "w", encoding="utf-8") as f:
    f.write("\n".join(s))
print(f"Painel salvo em {SAIDA} para @{USER}")
