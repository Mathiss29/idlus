#!/usr/bin/env python3
"""Sonde de l'Île des Wabbits (demande de Mathis : une zone pour le Dofus Cawotte).

Lit data/raw (import_dofusdb.py), repère les sous-zones de l'Île des Wabbits et le Château du Wa Wabbit,
lance tools/build_data.py avec cette zone en plus et dépose dans tools/probe/wabbit/ :
  - rapport.json : sous-zones, monstres, donjon trouvés ;
  - gamedata.js : les données complètes construites (le jeu n'en reprend que la nouvelle zone) ;
  - assets/<dossier>/ : les images nouvelles (absentes de assets/ du dépôt).
Ne touche ni à js/gamedata.js ni à assets/. Projet de fan non commercial, merci à DofusDB — contenu © Ankama Games.
"""
import json, glob, os, re, shutil, sys, unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'tools', 'probe', 'wabbit')
os.makedirs(OUT, exist_ok=True)


def load(ep):
    out = []
    for f in sorted(glob.glob(os.path.join(RAW, ep, 'page-*.json'))):
        out += json.load(open(f, encoding='utf-8'))
    return out


def fr(o):
    n = o.get('name') if isinstance(o, dict) else None
    return n.get('fr', '') if isinstance(n, dict) else str(n or '')


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')[:18]


areas = load('areas'); subareas = load('subareas'); dungeons = load('dungeons'); monsters = {m['id']: m for m in load('monsters')}
wab_areas = [a for a in areas if 'wabbit' in fr(a).lower()]
aids = {a['id'] for a in wab_areas}
dg = [d for d in dungeons if 'wabbit' in fr(d).lower()]
dg_subs = {d.get('subarea') for d in dungeons}
rep = {'areas': [(a['id'], fr(a)) for a in wab_areas], 'dungeons': [(d['id'], fr(d), d.get('subarea'), d.get('bosses')) for d in dg], 'subs': []}
subs = []
for s in subareas:
    if s.get('areaId') not in aids and 'wabbit' not in fr(s).lower():
        continue
    ok = [m for m in (monsters.get(x) for x in s.get('monsters') or []) if m and not m.get('isQuestMonster') and not m.get('isBoss') and m.get('race') != 78]
    lv = sorted(((m.get('grades') or [{}])[0].get('level', 0)) for m in ok)
    rep['subs'].append({'id': s['id'], 'name': fr(s), 'area': s.get('areaId'), 'dungeon': s['id'] in dg_subs, 'monsters': [(m['id'], fr(m), (m.get('grades') or [{}])[0].get('level')) for m in ok]})
    if ok and s['id'] not in dg_subs:
        n = fr(s)
        deco = 'cave' if re.search(r'Laborat|Grotte|Souterr|Terrier|Galerie', n) else 'beach' if re.search(r'Plage|Côte|Rivage|Berge', n) else 'forest' if re.search(r'Forêt|Bois', n) else 'meadow'
        subs.append((s['id'], 'wab_' + slug(n), deco))
json.dump(rep, open(os.path.join(OUT, 'rapport.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False)[:3000])
if not subs:
    print('aucune sous-zone Wabbit trouvée'); sys.exit(0)

# construction avec la zone en plus
src = open(os.path.join(ROOT, 'tools', 'build_data.py'), encoding='utf-8').read()
zone = "    {'id': 'wabbit', 'name': 'Île des Wabbits', 'desc': \"L'île du Wa Wabbit, de ses Wabbits et de ses champs de Cawottes.\", 'theme': 'meadow', 'requires': {'boss': 'cour_bouftou_royal'},\n     'subs': " + repr(subs) + "},\n"
i = src.index('\n]\nHIDDEN'); src = src[:i + 1] + zone + src[i + 1:]
access = subs[-1][1]
lines = ''.join(f"    ({d.get('subarea')}, 'wab_{slug(fr(d))}', '{access}'),\n" for d in dg if d.get('subarea') and d.get('bosses'))
j = src.index('\n]\nEXCLUDE_NAMES'); src = src[:j + 1] + lines + src[j + 1:]
open(os.path.join(OUT, 'build_data_patch.txt'), 'w', encoding='utf-8').write(zone + '\n' + lines)
sys.argv = ['build_data.py']
exec(compile(src, 'build_data.py', 'exec'), {'__name__': '__main__', '__file__': os.path.join(ROOT, 'tools', 'build_data.py')})
shutil.copy(os.path.join(ROOT, 'build', 'js', 'gamedata.js'), os.path.join(OUT, 'gamedata.js'))
n = 0
for d in os.listdir(os.path.join(ROOT, 'build', 'assets')):
    for f in os.listdir(os.path.join(ROOT, 'build', 'assets', d)):
        if not os.path.exists(os.path.join(ROOT, 'assets', d, f)):
            os.makedirs(os.path.join(OUT, 'assets', d), exist_ok=True)
            shutil.copy(os.path.join(ROOT, 'build', 'assets', d, f), os.path.join(OUT, 'assets', d, f)); n += 1
print('images nouvelles :', n)
