#!/usr/bin/env python3
"""Generate site/js/data.js from the raw LAN stat dumps.

Reads consolidated_player_stats.json + match_scoreboards/*.json + entry_stats/
and emits a single `const LAN_DATA = {...}` module so the site works when
opened straight from disk (file://) as well as when hosted.

Run from the repo root:  python3 tools/build_data.py
"""

import glob
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "js", "data.js")

TEAM_ORDER = ["SVEN", "AWISAVI"]


def pct(num, den):
    return round(100 * num / den, 1) if den else 0.0


def load_entry_stats():
    """Per-map opening-duel data from entry_stats/de_*.json.

    Two rounds in the LAN have no opening kill recorded (de_cache m14 r2,
    de_inferno m10 r12), so entry counts are the honest denominator here
    rather than the round count.
    """
    maps = []
    players = defaultdict(lambda: defaultdict(int))
    for path in sorted(glob.glob(os.path.join(ROOT, "entry_stats", "de_*.json"))):
        m = json.load(open(path, encoding="utf-8"))
        entries = sum(p["entry_kills"] for p in m["players"])
        maps.append(
            {
                "map": m["map"],
                "matches": m["matches_played"],
                "rounds": m["rounds"],
                "entries": entries,
                "converted": m["opening_kill_converted_rounds"],
                "pct": pct(m["opening_kill_converted_rounds"], entries),
            }
        )
        for p in m["players"]:
            acc = players[p["name"]]
            acc["entryKills"] += p["entry_kills"]
            acc["entryKillWins"] += p["entry_kill_round_wins"]
            acc["entryDeaths"] += p["entry_deaths"]
            acc["entryDeathWins"] += p["entry_death_round_wins"]

    maps.sort(key=lambda m: -m["pct"])
    return maps, players


def main():
    consolidated = json.load(
        open(os.path.join(ROOT, "consolidated_player_stats.json"), encoding="utf-8")
    )
    matches = sorted(
        (
            json.load(open(f, encoding="utf-8"))
            for f in glob.glob(os.path.join(ROOT, "match_scoreboards", "*.json"))
        ),
        key=lambda m: m["matchid"],
    )

    rounds_total = sum(sum(m["score"].values()) for m in matches)
    team_of = {p["name"]: p["team"] for p in consolidated["players"]}
    entry_maps, entry_players = load_entry_stats()

    # ---- matches -----------------------------------------------------------
    map_records = defaultdict(lambda: {t: 0 for t in TEAM_ORDER})
    series = {t: 0 for t in TEAM_ORDER}
    round_totals = {t: 0 for t in TEAM_ORDER}
    side_rounds = {"CT": 0, "T": 0}

    out_matches = []
    for m in matches:
        map_records[m["map"]][m["winner"]] += 1
        series[m["winner"]] += 1
        for t in TEAM_ORDER:
            round_totals[t] += m["score"][t]
        for side in ("CT", "T"):
            side_rounds[side] += m["rounds_secured"][side]

        teams = []
        for t in m["teams"]:
            players = sorted(t["players"], key=lambda p: -p["kills"])
            teams.append(
                {
                    "name": t["name"],
                    "startingSide": t["starting_side"],
                    "roundsWon": t["rounds_won"],
                    "won": t["name"] == m["winner"],
                    "players": [
                        {
                            "name": p["name"],
                            "kills": p["kills"],
                            "deaths": p["deaths"],
                            "assists": p["assists"],
                            "hs": p["hs_percent"],
                            "adr": p["adr"],
                            "utilDmg": p["utility_damage"],
                        }
                        for p in players
                    ],
                }
            )
        teams.sort(key=lambda t: TEAM_ORDER.index(t["name"]))

        out_matches.append(
            {
                "id": m["matchid"],
                "map": m["map"],
                "rounds": sum(m["score"].values()),
                "winner": m["winner"],
                "loser": [t for t in TEAM_ORDER if t != m["winner"]][0],
                "score": m["score"],
                "overtime": m["overtime"],
                "halfScores": m["half_scores"],
                "roundsSecured": m["rounds_secured"],
                "teams": teams,
            }
        )

    # ---- per-player, per-match series --------------------------------------
    per_match = defaultdict(dict)
    for m in matches:
        for t in m["teams"]:
            for p in t["players"]:
                per_match[p["name"]][m["matchid"]] = {
                    "matchId": m["matchid"],
                    "map": m["map"],
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "assists": p["assists"],
                    "hs": p["hs_percent"],
                    "adr": p["adr"],
                    "utilDmg": p["utility_damage"],
                    "won": t["name"] == m["winner"],
                }

    match_ids = [m["matchid"] for m in matches]

    out_players = []
    for p in consolidated["players"]:
        t = p["totals"]
        games = [per_match[p["name"]][mid] for mid in match_ids]
        e = entry_players[p["name"]]
        # Every opening duel has one killer and one victim, and exactly one
        # side wins the round — so entryRoundWinPct is zero-sum across the
        # lobby and sits at exactly 50% LAN-wide. It reads as above/below par.
        e_duels = e["entryKills"] + e["entryDeaths"]
        e_wins = e["entryKillWins"] + e["entryDeathWins"]
        out_players.append(
            {
                "entryKills": e["entryKills"],
                "entryKillWins": e["entryKillWins"],
                "entryKillWinPct": pct(e["entryKillWins"], e["entryKills"]),
                "entryDeaths": e["entryDeaths"],
                "entryDeathWins": e["entryDeathWins"],
                "entryDeathWinPct": pct(e["entryDeathWins"], e["entryDeaths"]),
                "entryDuels": e_duels,
                "entryRoundWins": e_wins,
                "entryRoundWinPct": pct(e_wins, e_duels),
                "name": p["name"],
                "team": p["team"],
                "steamid64": p["steamid64"],
                "kills": t["kills"],
                "deaths": t["deaths"],
                "assists": t["assists"],
                "damage": t["damage"],
                "adr": p["damage_per_round"],
                "kd": round(t["kills"] / t["deaths"], 2),
                "kpr": round(t["kills"] / rounds_total, 2),
                "dpr": round(t["deaths"] / rounds_total, 2),
                "apr": round(t["assists"] / rounds_total, 2),
                "hs": pct(t["head_shot_kills"], t["kills"]),
                "hsKills": t["head_shot_kills"],
                "accuracy": pct(t["shots_on_target_total"], t["shots_fired_total"]),
                "shotsFired": t["shots_fired_total"],
                "shotsHit": t["shots_on_target_total"],
                "entryCount": t["entry_count"],
                "entryWins": t["entry_wins"],
                "entryPct": pct(t["entry_wins"], t["entry_count"]),
                "firstKills": t["first_kills"],
                "clutchKills": t["clutch_kills"],
                "v1": t["v1_count"],
                "v1Wins": t["v1_wins"],
                "v1Pct": pct(t["v1_wins"], t["v1_count"]),
                "v2": t["v2_count"],
                "v2Wins": t["v2_wins"],
                "v2Pct": pct(t["v2_wins"], t["v2_count"]),
                "mvps": t["mvps"],
                "score": t["score"],
                "objective": t["objective"],
                "multi5k": t["enemy5ks"],
                "multi4k": t["enemy4ks"],
                "multi3k": t["enemy3ks"],
                "multi2k": t["enemy2ks"],
                "utilCount": t["utility_count"],
                "utilDmg": t["utility_damage"],
                "utilDmgPerRound": round(t["utility_damage"] / rounds_total, 2),
                "utilEnemies": t["utility_enemies"],
                "flashCount": t["flash_count"],
                "flashSuccesses": t["flash_successes"],
                "enemiesFlashed": t["enemies_flashed"],
                "killsPistol": t["kills_pistol"],
                "killsSniper": t["kills_sniper"],
                "killsKnife": t["kills_knife"],
                "killsTaser": t["kills_taser"],
                "equipmentValue": t["equipment_value"],
                "cashEarned": t["cash_earned"],
                "liveTime": t["live_time"],
                # live_time is seconds; per-round is the readable form
                "alivePerRound": round(t["live_time"] / rounds_total, 1),
                "clutchAttempts": t["v1_count"] + t["v2_count"],
                "clutchWins": t["v1_wins"] + t["v2_wins"],
                "clutchPct": pct(t["v1_wins"] + t["v2_wins"], t["v1_count"] + t["v2_count"]),
                "specialKills": (
                    t["kills_pistol"] + t["kills_sniper"] + t["kills_knife"] + t["kills_taser"]
                ),
                "games": games,
            }
        )

    out_players.sort(key=lambda p: -p["kd"])

    # ---- teams -------------------------------------------------------------
    out_teams = []
    for name in TEAM_ORDER:
        roster = [p for p in out_players if p["team"] == name]
        agg = {
            k: sum(p[k] for p in roster)
            for k in (
                "kills deaths assists damage hsKills utilDmg utilCount enemiesFlashed "
                "flashCount entryCount entryWins clutchKills firstKills mvps objective "
                "shotsFired shotsHit killsPistol killsSniper killsKnife killsTaser "
                "liveTime v1 v1Wins v2 v2Wins"
            ).split()
        }

        team_matches = []
        for m in out_matches:
            side = next(t for t in m["teams"] if t["name"] == name)
            k = sum(p["kills"] for p in side["players"])
            d = sum(p["deaths"] for p in side["players"])
            a = sum(p["assists"] for p in side["players"])
            n = m["rounds"]
            team_matches.append(
                {
                    "matchId": m["id"],
                    "map": m["map"],
                    "won": side["won"],
                    "roundsWon": side["roundsWon"],
                    "roundsLost": m["score"][m["loser"] if side["won"] else m["winner"]],
                    "kills": k,
                    "deaths": d,
                    "assists": a,
                    "avgAdr": round(
                        sum(p["adr"] for p in side["players"]) / len(side["players"]), 1
                    ),
                    "kd": round(k / d, 2) if d else 0,
                    "killsPerRound": round(k / n, 2),
                    "utilDmg": sum(p["utilDmg"] for p in side["players"]),
                    "startingSide": side["startingSide"],
                }
            )

        wins = [t for t in team_matches if t["won"]]
        losses = [t for t in team_matches if not t["won"]]
        best = max(team_matches, key=lambda t: t["roundsWon"] - t["roundsLost"])
        worst = min(team_matches, key=lambda t: t["roundsWon"] - t["roundsLost"])

        out_teams.append(
            {
                "name": name,
                "mapsWon": series[name],
                "mapsLost": len(matches) - series[name],
                "roundsWon": round_totals[name],
                "roundsLost": round_totals[[t for t in TEAM_ORDER if t != name][0]],
                "roster": [p["name"] for p in roster],
                "totals": agg,
                "kd": round(agg["kills"] / agg["deaths"], 2),
                "adr": round(agg["damage"] / rounds_total, 1),
                "hs": pct(agg["hsKills"], agg["kills"]),
                "accuracy": pct(agg["shotsHit"], agg["shotsFired"]),
                "entryPct": pct(agg["entryWins"], agg["entryCount"]),
                "matches": team_matches,
                "best": best,
                "worst": worst,
                "wins": len(wins),
                "losses": len(losses),
            }
        )

    out_map_records = [
        {
            "map": mp,
            "SVEN": rec["SVEN"],
            "AWISAVI": rec["AWISAVI"],
            "played": rec["SVEN"] + rec["AWISAVI"],
        }
        for mp, rec in sorted(
            map_records.items(), key=lambda kv: (-(kv[1]["SVEN"] + kv[1]["AWISAVI"]), kv[0])
        )
    ]

    # ---- headline / standout facts ----------------------------------------
    all_perfs = [
        {
            "name": p["name"],
            "team": p["team"],
            "map": g["map"],
            "matchId": g["matchId"],
            "adr": g["adr"],
            "kills": g["kills"],
            "deaths": g["deaths"],
            "won": g["won"],
        }
        for p in out_players
        for g in p["games"]
    ]
    top_perfs = sorted(all_perfs, key=lambda x: -x["adr"])[:5]

    champion = max(out_teams, key=lambda t: t["mapsWon"])
    mvp = max(out_players, key=lambda p: p["mvps"])

    entry_total_entries = sum(m["entries"] for m in entry_maps)
    entry_total_converted = sum(m["converted"] for m in entry_maps)
    out_entry = {
        "maps": entry_maps,
        "entries": entry_total_entries,
        "converted": entry_total_converted,
        "pct": pct(entry_total_converted, entry_total_entries),
        "roundsMissing": rounds_total - entry_total_entries,
        "best": entry_maps[0],
        "worst": entry_maps[-1],
        "teams": {
            t["name"]: pct(
                sum(p["entryKillWins"] for p in out_players if p["team"] == t["name"]),
                sum(p["entryKills"] for p in out_players if p["team"] == t["name"]),
            )
            for t in out_teams
        },
    }

    data = {
        "meta": {
            "title": "KOSLEP LAN 2026",
            "matchCount": len(matches),
            "roundsTotal": rounds_total,
            "playerCount": len(out_players),
            "mapPool": len(map_records),
            "overtimes": sum(1 for m in out_matches if m["overtime"]),
            "seriesScore": series,
            "roundTotals": round_totals,
            "sideRounds": side_rounds,
            "champion": champion["name"],
            "runnerUp": [t for t in TEAM_ORDER if t != champion["name"]][0],
            "mvp": mvp["name"],
            "damageGap": abs(
                out_teams[0]["totals"]["damage"] - out_teams[1]["totals"]["damage"]
            ),
            "aces": sum(p.get("multi5k", 0) for p in out_players),
        },
        "teamOrder": TEAM_ORDER,
        "teams": out_teams,
        "players": out_players,
        "matches": out_matches,
        "mapRecords": out_map_records,
        "entry": out_entry,
        "topPerformances": top_perfs,
        "matchIds": match_ids,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("// GENERATED FILE - edit tools/build_data.py and re-run instead.\n")
        fh.write("// python3 tools/build_data.py\n")
        fh.write("const LAN_DATA = ")
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write(";\n")

    print(f"wrote {OUT} ({os.path.getsize(OUT):,} bytes)")
    print(f"  {len(out_matches)} matches, {len(out_players)} players, {rounds_total} rounds")
    print(f"  series: {series}, rounds: {round_totals}")


if __name__ == "__main__":
    main()
