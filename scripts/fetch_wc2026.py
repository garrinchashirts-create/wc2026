#!/usr/bin/env python3
"""
WC2026 Match Tracker
Fetches real results from openfootball + martj42,
compares with ELO+Dixon-Coles model predictions,
saves to data/wc2026_tracker.json
"""
import requests, json, csv, math, io, os
from datetime import datetime, timezone

# ── Team name → our 3-letter code ─────────────────────────────────────────
NAME_MAP = {
    'Mexico':'MEX','South Africa':'AFS','South Korea':'COR','Czech Republic':'TCH',
    'Canada':'CAN','Bosnia & Herzegovina':'BOS','Bosnia and Herzegovina':'BOS',
    'USA':'EUA','United States':'EUA','Paraguay':'PAR','Qatar':'CAT',
    'Switzerland':'SUI','Brazil':'BRA','Morocco':'MAR','Haiti':'HAI','Scotland':'ESC',
    'Australia':'AUS','Turkey':'TUR','Germany':'ALE','Curaçao':'CUR','Ivory Coast':'CDM',
    'Ecuador':'EQU','Spain':'ESP','Costa Rica':'CRC','Argentina':'ARG','Algeria':'AGL',
    'France':'FRA','Senegal':'SEN','Iraq':'IRQ','Norway':'NOR','England':'ING',
    'Croatia':'CRO','Ghana':'GAN','Panama':'PAN','Portugal':'POR','DR Congo':'RDC',
    "D.R. Congo":'RDC','Uzbekistan':'UZB','Colombia':'COL','Netherlands':'HOL',
    'Japan':'JAP','Sweden':'SUE','Tunisia':'TUN','Belgium':'BEL','Egypt':'EGI',
    'Iran':'IRA','New Zealand':'NZE','Uruguay':'URU','Cape Verde':'CAB',
    'Saudi Arabia':'ARS','Austria':'AUT','Jordan':'JOR','Serbia':'SRB',
    "Côte d'Ivoire":'CDM', 'Ivory Coast':'CDM',
}

# ── ELO ratings (calibrated Jun 2026, cup26matches.com) ────────────────────
ELO = {
    'ESP':2074,'ARG':2064,'FRA':2060,'BRA':1994,'ING':2010,'POR':1970,
    'ALE':1927,'HOL':1930,'BEL':1895,'CRO':1880,'COL':1875,'URU':1870,
    'MEX':1850,'SEN':1830,'MAR':1825,'SUI':1820,'AUT':1815,'JAP':1810,
    'NOR':1800,'TUR':1795,'EQU':1785,'AUS':1780,'ESC':1775,'COR':1770,
    'EUA':1760,'CAN':1755,'SUE':1740,'AGL':1740,'EGI':1730,'CAT':1720,
    'ARS':1715,'TCH':1710,'IRA':1725,'RDC':1700,'CDM':1700,'IRQ':1690,
    'JOR':1685,'PAN':1650,'BOS':1760,'GAN':1680,'HAI':1650,'CAB':1620,
    'CUR':1640,'PAR':1660,'AFS':1720,'NZE':1600,'TUN':1695,'UZB':1670,
}
HOME_BONUS = {'MEX':100,'EUA':100,'CAN':80}
DC_RHO = -0.13

def poisson_pmf(k, lam):
    if lam <= 0: return 1.0 if k == 0 else 0.0
    p = math.exp(-lam)
    for i in range(1, k+1): p *= lam/i
    return p

def dc_tau(a, b, lam, mu):
    if a==0 and b==0: return 1 - lam*mu*DC_RHO
    if a==0 and b==1: return 1 + lam*DC_RHO
    if a==1 and b==0: return 1 + mu*DC_RHO
    if a==1 and b==1: return 1 - DC_RHO
    return 1.0

def match_prob(code_a, code_b, neutral=True):
    rA = ELO.get(code_a, 1650)
    rB = ELO.get(code_b, 1650)
    hb = 0 if neutral else (HOME_BONUS.get(code_a,0) - HOME_BONUS.get(code_b,0))
    lam = max(0.3, min(3.5, 1.35 + ((rA+hb)-rB)/400))
    mu  = max(0.3, min(3.5, 1.35 + (rB-(rA+hb/2))/400))
    wA=dr=wB=0.0
    for a in range(9):
        pA = poisson_pmf(a, lam)
        for b in range(9):
            tau = dc_tau(a, b, lam, mu)
            p = pA * poisson_pmf(b, mu) * tau
            if a>b: wA+=p
            elif a<b: wB+=p
            else: dr+=p
    tot = wA+dr+wB
    return {
        'winA': round(wA/tot,4), 'draw': round(dr/tot,4), 'winB': round(wB/tot,4),
        'xgA': round(lam,2), 'xgB': round(mu,2),
        'eloA': ELO.get(code_a,1650), 'eloB': ELO.get(code_b,1650)
    }

def to_code(name):
    return NAME_MAP.get(name, name[:3].upper())

# ── Fetch openfootball (scores + upcoming) ─────────────────────────────────
print("Fetching openfootball...")
r = requests.get("https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json", timeout=20)
of_data = r.json()

# ── Fetch martj42 (confirmed results with scorelines) ─────────────────────
print("Fetching martj42 results...")
r2 = requests.get("https://raw.githubusercontent.com/martj42/international_results/master/results.csv", timeout=30)
reader = csv.DictReader(io.StringIO(r2.text))
martj42 = {}
for row in reader:
    if 'FIFA World Cup' in row.get('tournament','') and 'qualification' not in row['tournament'].lower():
        key = f"{row['date']}_{to_code(row['home_team'])}_{to_code(row['away_team'])}"
        try:
            hs = int(row['home_score']) if row['home_score'] not in ('NA','') else None
            as_ = int(row['away_score']) if row['away_score'] not in ('NA','') else None
        except: hs=as_=None
        martj42[key] = {'score1': hs, 'score2': as_, 'city': row.get('city',''), 'neutral': row.get('neutral','TRUE')=='TRUE'}

print(f"martj42 WC2026 rows: {len(martj42)}")

# ── Build tracker ──────────────────────────────────────────────────────────
matches = []
model_correct = 0
model_total = 0
total_rps = 0.0

for m in of_data['matches']:
    code_a = to_code(m['team1'])
    code_b = to_code(m['team2'])
    date = m['date']
    neutral = True  # most WC matches at neutral venues

    # Get model prediction
    pred = match_prob(code_a, code_b, neutral)

    # Get real score
    score = m.get('score', {})
    ft = score.get('ft') if score else None
    
    # Also check martj42
    key = f"{date}_{code_a}_{code_b}"
    m42 = martj42.get(key, {})
    
    if ft:
        g1, g2 = ft[0], ft[1]
    elif m42.get('score1') is not None:
        g1, g2 = m42['score1'], m42['score2']
    else:
        g1, g2 = None, None

    played = g1 is not None and g2 is not None

    entry = {
        'date': date,
        'time': m.get('time',''),
        'group': m.get('group',''),
        'round': m.get('round',''),
        'home': code_a,
        'away': code_b,
        'home_name': m['team1'],
        'away_name': m['team2'],
        'city': m.get('ground', m42.get('city','')),
        'played': played,
        'score1': g1,
        'score2': g2,
        'model': pred,
    }

    # Model accuracy
    if played:
        actual = 'A' if g1>g2 else 'B' if g2>g1 else 'D'
        pred_winner = 'A' if pred['winA']>pred['draw'] and pred['winA']>pred['winB'] else \
                      'B' if pred['winB']>pred['draw'] and pred['winB']>pred['winA'] else 'D'
        correct = actual == pred_winner
        if correct: model_correct += 1
        model_total += 1

        # RPS (Ranked Probability Score) — lower is better
        # Ordered: [A wins, draw, B wins]
        p = [pred['winA'], pred['draw'], pred['winB']]
        o = [1 if actual=='A' else 0, 1 if actual=='D' else 0, 1 if actual=='B' else 0]
        rps = sum((sum(p[:i+1]) - sum(o[:i+1]))**2 for i in range(2)) / 2
        total_rps += rps

        entry['actual'] = actual
        entry['model_correct'] = correct
        entry['rps'] = round(rps, 4)

    matches.append(entry)

# Sort by date
matches.sort(key=lambda x: x['date'])

# Summary
summary = {
    'updated_at': datetime.now(timezone.utc).isoformat(),
    'played': model_total,
    'model_correct': model_correct,
    'accuracy': round(model_correct/model_total*100, 1) if model_total else 0,
    'avg_rps': round(total_rps/model_total, 4) if model_total else 0,
    'coin_flip_rps': 0.245,
}

output = {'summary': summary, 'matches': matches}

os.makedirs('data', exist_ok=True)
with open('data/wc2026_tracker.json', 'w') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved data/wc2026_tracker.json")
print(f"   Total matches: {len(matches)}")
print(f"   Played: {model_total}")
print(f"   Model accuracy: {summary['accuracy']}%")
print(f"   Avg RPS: {summary['avg_rps']} (coin-flip: 0.245)")
print(f"\nResults so far:")
for m in matches:
    if m['played']:
        icon = '✅' if m.get('model_correct') else '❌'
        print(f"  {icon} {m['date']} {m['home_name']} {m['score1']}-{m['score2']} {m['away_name']} | model: {m['model']['winA']:.0%}/{m['model']['draw']:.0%}/{m['model']['winB']:.0%}")
