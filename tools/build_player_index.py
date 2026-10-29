"""Build the Second Look player index.

Lists every league-season each Wyscout ID appears in, so Second Look can show a
player's full history without downloading every league file.

Run from the root of the Wyscout_Data repository:
    python tools/build_player_index.py

Writes:
    player_index/leagues.csv        idx,gender,league,season
    player_index/shard_000.csv ...  wyscout_id,idx,minutes   (256 files, split by ID)
"""
import csv, io, os, sys, urllib.request

LOOKUPS = {
    'Men': 'https://raw.githubusercontent.com/griffisben/Wyscout_Prospect_Research/main/league_info_lookup.csv',
    'Women': 'https://raw.githubusercontent.com/griffisben/Wyscout_Prospect_Research/main/league_info_lookup_women.csv',
}
FOLDERS = {'Men': 'Main App', 'Women': os.path.join('Main App', 'Women')}
CHARS = str.maketrans({'ü': 'u', 'ó': 'o', 'ö': 'o', 'ã': 'a', 'ç': 'c', 'é': 'e', 'ê': 'e', 'á': 'a', 'â': 'a'})
SHARDS = 256
OUT = 'player_index'


def read_lookup(url):
    with urllib.request.urlopen(url) as r:
        text = r.read().decode('utf-8-sig')
    return [row for row in csv.DictReader(io.StringIO(text)) if row.get('League')]


def to_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def main():
    leagues, shards = [], [[] for _ in range(SHARDS)]
    found = missing = 0
    for gender, url in LOOKUPS.items():
        for row in read_lookup(url):
            name = f"{row['League']} {row['Season']}"
            path = os.path.join(FOLDERS[gender], name.translate(CHARS) + '.csv')
            if not os.path.exists(path):
                missing += 1
                continue
            idx = len(leagues)
            leagues.append((idx, gender, row['League'], row['Season']))
            found += 1
            with open(path, newline='', encoding='utf-8-sig') as f:
                for p in csv.DictReader(f):
                    wid = to_int(p.get('Wyscout id'))
                    if wid is None:
                        continue
                    mins = to_int(p.get('Minutes played')) or 0
                    shards[abs(wid) % SHARDS].append((wid, idx, mins))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'leagues.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['idx', 'gender', 'league', 'season'])
        w.writerows(leagues)
    rows = 0
    for i, shard in enumerate(shards):
        shard.sort()
        with open(os.path.join(OUT, f'shard_{i:03d}.csv'), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f, lineterminator='\n')
            w.writerow(['wyscout_id', 'idx', 'minutes'])
            w.writerows(shard)
        rows += len(shard)
    print(f'{found} league-seasons indexed, {missing} listed but not found, {rows} player rows.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
