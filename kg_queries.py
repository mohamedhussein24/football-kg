# ===========================================
# kg_queries.py — Runs ALL required SPARQL queries
# ===========================================

from rdflib import Graph, Namespace, RDFS
import pandas as pd

INPUT_TTL = "football_kg_extended.ttl"

print("Loading graph:", INPUT_TTL)
g = Graph()
g.parse(INPUT_TTL, format="turtle")
print("Graph loaded. Total triples:", len(g))

ONT = Namespace("http://www.semanticSports.org/ontology#")
EX = Namespace("http://www.semanticSports.org/data/")


# Helper function to run and print results
def run_query(query, csv_output=None):
    res = g.query(query)
    
    cols = [str(v) for v in res.vars]
    rows = []

    for r in res:
        row = []
        for val in r:
            if val is None:
                row.append("")
                continue

            # Replace URI with label if possible
            if isinstance(val, str):
                row.append(val)
                continue

            label = None
            for lbl in g.objects(val, RDFS.label):
                label = str(lbl)
                break

            row.append(label if label else str(val))
        rows.append(row)

    df = pd.DataFrame(rows, columns=cols)
    print("\n===========================================")
    print(df)
    print("===========================================\n")

    if csv_output:
        df.to_csv(csv_output, index=False)
        print("Saved:", csv_output)


# =========================================================
# 1️⃣ SELECT QUERIES (5 required)
# =========================================================

# SELECT 1 — Top goal scorers
q1 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel (SUM(?g) AS ?totalGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?p .
  ?p ont:scoredGoals ?g .
}
GROUP BY ?playerLabel
ORDER BY DESC(?totalGoals)
LIMIT 15
"""
run_query(q1, "query_top_scorers.csv")


# SELECT 2 — Players per team
q2 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel
WHERE {
  ?player a ont:Player .
  ?player ont:hasTeam ?team .
  ?player rdfs:label ?playerLabel .
  ?team rdfs:label ?teamLabel .
}
ORDER BY ?teamLabel ?playerLabel
"""
run_query(q2, "query_players_per_team.csv")


# ===========================================
# UPDATED SELECT 3 — Only incorrect DBpedia birthPlaces
# ===========================================

q3 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?birthPlace
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:birthPlace ?birthPlace }

  FILTER(BOUND(?birthPlace))

  # keep only wrong DBpedia values
  FILTER(CONTAINS(LCASE(STR(?birthPlace)), "national football team"))

  # exclude Haaland's incorrect value (generic, not by name)
  FILTER(!CONTAINS(LCASE(STR(?birthPlace)), "england national football team"))
}
ORDER BY ?playerLabel
"""
run_query(q3, "query_filtered_birthplace.csv")


# SELECT 4 — Goals > 25
q4 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?goals
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?p .
  ?p ont:scoredGoals ?goals .
  FILTER(?goals > 25)
}
ORDER BY DESC(?goals)
"""
run_query(q4, "query_high_scorers.csv")


# SELECT 5 — Flexible UNION: Real Madrid or Arsenal
q5 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT DISTINCT ?playerLabel ?teamLabel
WHERE {
  ?player a ont:Player .
  ?player ont:hasTeam ?team .
  ?player rdfs:label ?playerLabel .
  ?team rdfs:label ?teamLabel .

  FILTER(
    CONTAINS(LCASE(?teamLabel), "realmadrid") ||
    CONTAINS(LCASE(?teamLabel), "arsenal")
  )
}
ORDER BY ?teamLabel ?playerLabel
"""
run_query(q5, "query_union_teams.csv")


# =========================================================
# 2️⃣ CONSTRUCT QUERIES
# =========================================================

# CONSTRUCT 1 — Minimal player profile
q6 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
CONSTRUCT {
  ?player a ont:Player .
  ?player ont:hasTeam ?team .
  ?player rdfs:label ?label .
}
WHERE {
  ?player a ont:Player .
  ?player ont:hasTeam ?team .
  ?player rdfs:label ?label .
}
"""
constructed1 = g.query(q6)
Graph().parse(data=constructed1.serialize(format="turtle"), format="turtle") \
       .serialize("construct_player_profiles.ttl")
print("Saved construct_player_profiles.ttl")


# CONSTRUCT 2 — Team total goals
q7 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
CONSTRUCT {
  ?team ont:totalGoals ?totalGoals .
}
WHERE {
  SELECT ?team (SUM(?g) AS ?totalGoals)
  WHERE {
    ?player a ont:Player .
    ?player ont:hasTeam ?team .
    ?player ont:hasPerformance ?p .
    ?p ont:scoredGoals ?g .
  }
  GROUP BY ?team
}
"""
constructed2 = g.query(q7)
Graph().parse(data=constructed2.serialize(format="turtle"), format="turtle") \
       .serialize("construct_team_goals.ttl")
print("Saved construct_team_goals.ttl")


# =========================================================
# 3️⃣ ASK QUERY
# =========================================================

q8 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
ASK {
  ?player a ont:Player .
  ?player ont:nationality ?nat .
}
"""
ask_result = g.query(q8)
print("\nASK Query: Is there at least one player with nationality data?")
print("Result:", "YES" if ask_result.askAnswer else "NO")


# =========================================================
# 4️⃣ DESCRIBE QUERY
# =========================================================

q9 = """
DESCRIBE <http://www.semanticSports.org/data/LionelMessi>
"""
describe_result = g.query(q9)

with open("describe_messi.ttl", "wb") as f:
    f.write(describe_result.serialize(format="turtle"))
print("\nSaved describe_messi.ttl")


print("\n===========================================")
print("ALL QUERIES EXECUTED SUCCESSFULLY")
print("===========================================\n")
