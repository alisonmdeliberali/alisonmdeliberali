"""
Desenha a "cidade dos commits": cada prédio é uma semana (ou um repositório),
e agentes-robô voam pela cidade entregando código para o prédio em obra.
Tudo em SVG + CSS/SMIL puro, então anima direto no README do GitHub.
"""
import random
from xml.sax.saxutils import escape

ALTURA = 214

CSS = """
  .estrela{fill:#fff;animation:brilho 3s ease-in-out infinite}
  @keyframes brilho{0%,100%{opacity:.2}50%{opacity:1}}
  .janela{fill:var(--janela);animation:luz 5s ease-in-out infinite}
  .apagada{fill:var(--janela-off)}
  @keyframes luz{0%,100%{opacity:.25}45%,60%{opacity:1}}
  .flutua{animation:flutua 1.6s ease-in-out infinite}
  @keyframes flutua{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
  .chama{animation:chama .25s steps(2) infinite}
  @keyframes chama{50%{transform:scaleY(.55)}}
  .chama{transform-box:fill-box;transform-origin:top}
  .olho{animation:pisca 4s infinite}
  .olho{transform-box:fill-box;transform-origin:center}
  @keyframes pisca{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
  .antena{animation:antena 1.2s ease-in-out infinite}
  @keyframes antena{50%{fill:#E5534B}}
  .farol{animation:antena 1s steps(2) infinite}
  .obra{transform-box:fill-box;transform-origin:bottom;animation:sobe 9s ease-in-out infinite}
  @keyframes sobe{0%{transform:scaleY(.82)}55%,100%{transform:scaleY(1)}}
  .laser{animation:laser 2s ease-in-out infinite}
  @keyframes laser{0%,100%{opacity:.15}50%{opacity:.6}}
"""


def robo(cor, rotulo=""):
    """Um agentezinho com visor, antena e propulsor."""
    extra = f'<text x="0" y="-22" text-anchor="middle" style="font-size:9px;fill:var(--suave)">{escape(rotulo)}</text>' if rotulo else ""
    return f"""<g class="flutua">{extra}
  <line x1="0" y1="-11" x2="0" y2="-16" style="stroke:var(--tinta);stroke-width:1.5"/>
  <circle class="antena" cx="0" cy="-17" r="2.2" style="fill:#F2B33D"/>
  <rect x="-10" y="-11" width="20" height="15" rx="5" style="fill:{cor}"/>
  <rect x="-7" y="-8" width="14" height="7" rx="3" style="fill:#0F1730"/>
  <circle class="olho" cx="-3" cy="-4.5" r="1.5" style="fill:#2FBF9B"/>
  <circle class="olho" cx="3" cy="-4.5" r="1.5" style="fill:#2FBF9B"/>
  <path class="chama" d="M-4 4 L0 11 L4 4Z" style="fill:#F2B33D"/>
</g>"""


def desenhar_cidade(largura, valores, legenda, mensagens, semente):
    """valores: lista de números (o último é o prédio em obra)."""
    rnd = random.Random(semente)
    CW, CH, chao = largura, ALTURA, 176
    n = max(len(valores), 1)
    mx = max(valores) if valores and max(valores) > 0 else 1
    slot = (CW - 70) / n
    bw = min(34, slot * 0.62)
    prof = bw * 0.35
    s, css = [], [CSS]
    a = s.append

    a(f'<clipPath id="recorte"><rect width="{CW}" height="{CH}" rx="12"/></clipPath>')
    a('<g clip-path="url(#recorte)">')
    a(f'<rect width="{CW}" height="{CH}" style="fill:var(--ceu)"/>')
    a('<g style="opacity:var(--estrelas)">')
    for _ in range(30):
        a(f'<circle class="estrela" cx="{rnd.uniform(10, CW - 10):.0f}" cy="{rnd.uniform(40, 110):.0f}" '
          f'r="{rnd.choice([0.7, 1, 1.4])}" style="animation-delay:{rnd.uniform(0, 3):.1f}s"/>')
    a('</g>')
    a(f'<circle cx="{CW * 0.72:.0f}" cy="30" r="12" style="fill:var(--astro)"/>')

    # chão e rua
    a(f'<rect y="{chao}" width="{CW}" height="{CH - chao}" style="fill:var(--chao)"/>')
    a(f'<line x1="0" y1="{chao + 20}" x2="{CW}" y2="{chao + 20}" style="stroke:var(--faixa);stroke-width:2;stroke-dasharray:14 10"/>')

    alvo_x = alvo_topo = None
    i_max = valores.index(max(valores)) if valores else -1
    for i, v in enumerate(valores):
        h = 18 + 104 * v / mx
        x = 35 + i * slot + (slot - bw) / 2
        topo = chao - h
        d6 = prof * 0.6
        em_obra = i == n - 1
        frente, lado, teto = ("#2F6FEB", "#1F55C4", "#5A8FF2") if em_obra else ("var(--predio)", "var(--lado)", "var(--teto)")
        a(f'<g class="{"obra" if em_obra else ""}">')
        a(f'<polygon points="{x + bw},{topo} {x + bw + prof},{topo - d6} {x + bw + prof},{chao - d6} {x + bw},{chao}" style="fill:{lado}"/>')
        a(f'<polygon points="{x},{topo} {x + prof},{topo - d6} {x + bw + prof},{topo - d6} {x + bw},{topo}" style="fill:{teto}"/>')
        a(f'<rect x="{x:.1f}" y="{topo:.1f}" width="{bw:.1f}" height="{h:.1f}" style="fill:{frente}"/>')
        cols = 3 if bw > 26 else 2
        passo_x = bw / cols
        y = topo + 7
        while y < chao - 9:
            for c in range(cols):
                wx = x + c * passo_x + (passo_x - 5) / 2
                if rnd.random() < 0.3:
                    a(f'<rect class="apagada" x="{wx:.1f}" y="{y:.1f}" width="5" height="6" rx="1"/>')
                else:
                    a(f'<rect class="janela" x="{wx:.1f}" y="{y:.1f}" width="5" height="6" rx="1" '
                      f'style="animation-delay:{rnd.uniform(0, 5):.1f}s;animation-duration:{rnd.uniform(3, 8):.1f}s"/>')
            y += 11
        a('</g>')
        if i == i_max and not em_obra:  # antena com farol no prédio mais alto
            a(f'<line x1="{x + bw / 2}" y1="{topo}" x2="{x + bw / 2}" y2="{topo - 14}" style="stroke:var(--lado);stroke-width:2"/>')
            a(f'<circle class="farol" cx="{x + bw / 2}" cy="{topo - 15}" r="2.5" style="fill:#F2B33D"/>')
        if em_obra:
            alvo_x, alvo_topo = x + bw / 2, topo
            gx = x + bw + prof + 6
            a(f'<line x1="{gx}" y1="{chao}" x2="{gx}" y2="{topo - 34}" style="stroke:#F2B33D;stroke-width:3"/>')
            a(f'<line x1="{gx + 8}" y1="{topo - 32}" x2="{x - 10}" y2="{topo - 32}" style="stroke:#F2B33D;stroke-width:3"/>')
            a(f'<g><line x1="{x + 4}" y1="{topo - 32}" x2="{x + 4}" y2="{topo - 12}" style="stroke:var(--tinta);stroke-width:1"/>'
              f'<rect x="{x}" y="{topo - 12}" width="8" height="5" style="fill:#E5534B"/>'
              f'<animateTransform attributeName="transform" type="rotate" values="-10 {x + 4} {topo - 32};10 {x + 4} {topo - 32};-10 {x + 4} {topo - 32}" dur="3s" repeatCount="indefinite"/></g>')

    # carrinho passando na rua
    a(f'<g style="animation:carro 11s linear infinite"><rect x="0" y="{chao + 9}" width="22" height="8" rx="3" style="fill:#E5534B"/>'
      f'<rect x="5" y="{chao + 5}" width="11" height="6" rx="2" style="fill:#E5534B"/>'
      f'<circle cx="5" cy="{chao + 18}" r="2.5" style="fill:var(--tinta)"/><circle cx="17" cy="{chao + 18}" r="2.5" style="fill:var(--tinta)"/></g>')
    css.append(f"@keyframes carro{{from{{transform:translateX(-40px)}}to{{transform:translateX({CW + 40}px)}}}}")

    # agente entregador: chega voando, solta o bloco de código na obra e vai embora
    if alvo_x is not None:
        oy = alvo_topo - 58
        css.append(f"""@keyframes entrega{{0%{{transform:translate(-40px,30px)}}40%,58%{{transform:translate({alvo_x:.0f}px,{oy:.0f}px)}}100%{{transform:translate({CW + 40}px,20px)}}}}
  @keyframes bloco{{0%{{transform:translate(-40px,48px);opacity:1}}40%{{transform:translate({alvo_x:.0f}px,{oy + 18:.0f}px);opacity:1}}
  52%{{transform:translate({alvo_x:.0f}px,{alvo_topo - 8:.0f}px);opacity:1}}58%,100%{{transform:translate({alvo_x:.0f}px,{alvo_topo - 8:.0f}px);opacity:0}}}}""")
        a(f'<g style="animation:bloco 9s ease-in-out infinite"><rect x="-11" y="-7" width="22" height="13" rx="3" style="fill:#2FBF9B"/>'
          f'<text x="0" y="3" text-anchor="middle" style="font-size:9px;font-weight:700;fill:#0F1730">&lt;/&gt;</text></g>')
        a(f'<g style="animation:entrega 9s ease-in-out infinite">{robo("#2F6FEB", "deploy")}</g>')

    # agente revisor: patrulha a cidade com um laser de code review
    css.append(f"@keyframes ronda{{0%,100%{{transform:translate(60px,96px)}}50%{{transform:translate({CW * 0.62:.0f}px,96px)}}}}")
    a(f'<g style="animation:ronda 16s ease-in-out infinite">'
      f'<path class="laser" d="M-3 10 L-14 {chao - 96} L14 {chao - 96} L3 10Z" style="fill:#8B6FE8"/>{robo("#8B6FE8", "review")}</g>')

    # agente que fica no canto tomando café... digo, testando
    css.append("@keyframes teste{0%,100%{transform:translate(" + f"{CW - 110}px,118px" + ")}50%{transform:translate(" + f"{CW - 150}px,104px" + ")}}")
    a(f'<g style="animation:teste 7s ease-in-out infinite">{robo("#2FBF9B", "testes")}</g>')

    # terminal com mensagens de commit sendo digitadas
    a('<rect x="14" y="12" width="300" height="24" rx="6" style="fill:#0F1730;opacity:.92"/>')
    a('<circle cx="26" cy="24" r="3" style="fill:#E5534B"/><circle cx="36" cy="24" r="3" style="fill:#F2B33D"/><circle cx="46" cy="24" r="3" style="fill:#2FBF9B"/>')
    ciclo = 4 * len(mensagens)
    for k, msg in enumerate(mensagens):
        largura_txt = 7 * len(msg) + 10
        inicio, meio, fim = k * 4 / ciclo, (k * 4 + 2) / ciclo, (k * 4 + 3.9) / ciclo
        a(f'<clipPath id="digita{k}"><rect x="58" y="14" height="20" width="0">'
          f'<animate attributeName="width" dur="{ciclo}s" repeatCount="indefinite" '
          f'keyTimes="0;{inicio:.3f};{meio:.3f};{fim:.3f};{fim + 0.002:.3f};1" values="0;0;{largura_txt};{largura_txt};0;0"/>'
          f'</rect></clipPath>')
        a(f'<text x="60" y="28" clip-path="url(#digita{k})" style="font-family:ui-monospace,Consolas,monospace;font-size:11px;fill:#C9F2E5">{escape(msg)}</text>')

    a(f'<text x="{CW - 14}" y="{CH - 6}" text-anchor="end" style="font-size:10px;fill:var(--suave)">{escape(legenda)}</text>')
    a('</g>')
    return "\n".join(s), "\n".join(css)
