# ===========================================
# kg_pipeline.py  — FIXED VERSION
# ===========================================

import random
from datetime import datetime, timedelta
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.namespace import OWL
import pandas as pd
from pyshacl import validate
import os
import requests

# Optional: for Fuseki upload
from SPARQLWrapper import SPARQLWrapper, POST

# Optional reasoning (OWL-RL)
try:
    from owlrl import OWLRL_Semantics
    OWL_RL_AVAILABLE = True
except Exception:
    OWL_RL_AVAILABLE = False


# ===========================================
# CONFIG
# ===========================================

ONTOLOGY_FILE = "Football Web Semantics New.owl.rdf"
OUTPUT_TTL = "football_kg_extended.ttl"
SHACL_FILE = "shacl_shapes.ttl"
FUSEKI_ENDPOINT = "http://localhost:3030/footballKG/data"


# ===========================================
# LOAD BASE ONTOLOGY
# ===========================================

g = Graph()
print("Loading ontology:", ONTOLOGY_FILE)

g.parse(
    r"file:///C:/Users/SE7S/Downloads/Web%20Science/football-kg/Football%20Web%20Semantics%20New.owl.rdf",
    format="xml"
)

print("Base triples:", len(g))


# ===========================================
# NAMESPACES
# ===========================================

ONT = Namespace("http://www.semanticSports.org/ontology#")
EX = Namespace("http://www.semanticSports.org/data/")

g.bind("ont", ONT)
g.bind("ex", EX)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)


# ===========================================
# REMOVE OLD MAC ALLISTER PERFORMANCE DATA
# ===========================================

MAC = URIRef("http://www.semanticSports.org/ontology#AlexisMacAllister")

for pm in g.objects(MAC, ONT.hasPerformance):
    for p, o in g.predicate_objects(pm):
        g.remove((pm, p, o))
    g.remove((pm, None, None))

g.remove((MAC, ONT.hasPerformance, None))


# ===========================================
# REAL FOOTBALL PLAYERS + TEAMS
# ===========================================

real_players = {
    "CristianoRonaldo": {"team": "AlNassr", "goals": 35},
    "SadioMane": {"team": "AlNassr", "goals": 16},
    "AndersonTalisca": {"team": "AlNassr", "goals": 27},

    "LionelMessi": {"team": "InterMiami", "goals": 21},

    "KylianMbappe": {"team": "RealMadrid", "goals": 44},
    "ViniciusJr": {"team": "RealMadrid", "goals": 24},
    "JudeBellingham": {"team": "RealMadrid", "goals": 23},
    "LukaModric": {"team": "RealMadrid", "goals": 4},

    "ErlingHaaland": {"team": "ManchesterCity", "goals": 52},
    "KevinDeBruyne": {"team": "ManchesterCity", "goals": 10},
    "PhilFoden": {"team": "ManchesterCity", "goals": 19},

    "NeymarJr": {"team": "AlHilal", "goals": 13},
    "AleksandarMitrovic": {"team": "AlHilal", "goals": 28},
    "RubenNeves": {"team": "AlHilal", "goals": 6},

    "HarryKane": {"team": "BayernMunich", "goals": 42},
    "JamalMusiala": {"team": "BayernMunich", "goals": 12},

    "HeungMinSon": {"team": "Tottenham", "goals": 24},
    "JamesMaddison": {"team": "Tottenham", "goals": 6},

    "OusmaneDembele": {"team": "PSG", "goals": 11},

    "RobertLewandowski": {"team": "Barcelona", "goals": 33},

    # Liverpool real players
    "MohamedSalah": {"team": "LiverpoolFC", "goals": 25},
    "LuisDiaz": {"team": "LiverpoolFC", "goals": 11},
    "DarwinNunez": {"team": "LiverpoolFC", "goals": 15},
    "TrentAlexanderArnold": {"team": "LiverpoolFC", "goals": 4},
    "VirgilVanDijk": {"team": "LiverpoolFC", "goals": 5},
    "AlexisMacAllister": {"team": "LiverpoolFC", "goals": 7},
    "CodyGakpo": {"team": "LiverpoolFC", "goals": 10},
}


# ===========================================
# CREATE TEAMS
# ===========================================

teams_set = set([info["team"] for info in real_players.values()])
teams = {}

for team_label in teams_set:
    team_uri = EX[team_label]
    teams[team_label] = team_uri

    g.add((team_uri, RDF.type, ONT.Team))
    g.add((team_uri, RDFS.label, Literal(team_label, datatype=XSD.string)))
    

# ----------------- MERGE ONTOLOGY TEAMS WITH INSTANCE TEAMS -----------------

for team_label, ex_team_uri in teams.items():
    ont_team_uri = URIRef(str(ONT) + team_label)
    
    if (ont_team_uri, None, None) in g:
        g.add((ex_team_uri, OWL.sameAs, ont_team_uri))
        g.add((ont_team_uri, OWL.sameAs, ex_team_uri))
        print(f"Merged team: {team_label} → owl:sameAs applied")


# ===========================================
# MATCH GENERATION
# ===========================================

matches = []
start_date = datetime(2024, 9, 1, 15, 0)
team_list = list(teams.values())

for i in range(1, 13):
    m = EX[f"Match{i}"]
    matches.append(m)

    g.add((m, RDF.type, ONT.Match))
    g.add((m, ONT.matchDate, Literal((start_date + timedelta(days=7 * i)).isoformat(), datatype=XSD.dateTime)))

    if len(team_list) >= 2:
        t1, t2 = random.sample(team_list, 2)
        tournament_uri = EX["GlobalTournament"]
        g.add((m, ONT.partOfTournament, tournament_uri))
        g.add((t1, ONT.participatesIn, tournament_uri))
        g.add((t2, ONT.participatesIn, tournament_uri))


# ===========================================
# CREATE REAL PLAYER INDIVIDUALS + PERFORMANCE
# ===========================================

positions = [ONT.Forward, ONT.Midfielder, ONT.Defender, ONT.Goalkeeper]

for player_label, info in real_players.items():

    # Check if player already exists in ontology namespace
    existing_ont_uri = URIRef(str(ONT) + player_label)
    player_exists_in_ontology = (existing_ont_uri, RDF.type, ONT.Player) in g
    
    # Always use EX namespace for new data
    player_uri = EX[player_label]

    # Always add player type and label
    g.add((player_uri, RDF.type, ONT.Player))
    g.add((player_uri, RDFS.label, Literal(player_label, datatype=XSD.string)))

    team_uri = teams[info["team"]]
    g.add((player_uri, ONT.hasTeam, team_uri))
    g.add((player_uri, ONT.hasPosition, random.choice(positions)))

    perf_uri = EX[f"Perf_{player_label}"]
    g.add((perf_uri, RDF.type, ONT.PerformanceMetric))

    match_uri = random.choice(matches)
    g.add((perf_uri, ONT.forMatch, match_uri))
    g.add((player_uri, ONT.playedIn, match_uri))

    goals = info["goals"]
    assists = max(0, int(goals * 0.15))
    minutes = random.randint(200, 3000)
    rating = round(min(10.0, 5.0 + goals / 10 + random.uniform(-0.3, 0.6)), 1)

    g.add((perf_uri, ONT.scoredGoals, Literal(goals, datatype=XSD.integer)))
    g.add((perf_uri, ONT.madeAssists, Literal(assists, datatype=XSD.integer)))
    g.add((perf_uri, ONT.playedMinutes, Literal(minutes, datatype=XSD.integer)))
    g.add((perf_uri, ONT.hasPerformanceRating, Literal(rating, datatype=XSD.float)))

    g.add((player_uri, ONT.hasPerformance, perf_uri))


print("After real-player generation triples:", len(g))


# ----------------- MERGE ONTOLOGY PLAYERS WITH INSTANCE PLAYERS -----------------

for player_label in real_players.keys():
    ont_player_uri = URIRef(str(ONT) + player_label)
    ex_player_uri = EX[player_label]
    
    if (ont_player_uri, None, None) in g:
        g.add((ex_player_uri, OWL.sameAs, ont_player_uri))
        g.add((ont_player_uri, OWL.sameAs, ex_player_uri))
        print(f"Merged player: {player_label} → owl:sameAs applied")


# ===========================================
# VALIDATE AND CLEAN GRAPH DATA
# ===========================================

print("\nValidating graph structure...")

# Remove any triples where literals are used as subjects
invalid_triples = []
for s, p, o in g:
    if isinstance(s, Literal):
        invalid_triples.append((s, p, o))
        print(f"WARNING: Found literal as subject: {s} -- removing")

for triple in invalid_triples:
    g.remove(triple)

if invalid_triples:
    print(f"Removed {len(invalid_triples)} invalid triples")

# Ensure clean numeric typing
for s, p, o in list(g.triples((None, ONT.playedMinutes, None))):
    if isinstance(o, Literal) and o.datatype is None:
        try:
            g.set((s, p, Literal(int(str(o)), datatype=XSD.integer)))
        except:
            pass

print("Graph validation complete")


# ===========================================
# EXTERNAL DATA INTEGRATION - DBPEDIA
# ===========================================

# Add new properties to ontology if they don't exist
g.add((ONT.birthDate, RDF.type, RDF.Property))
g.add((ONT.birthPlace, RDF.type, RDF.Property))
g.add((ONT.height, RDF.type, RDF.Property))
g.add((ONT.nationality, RDF.type, RDF.Property))
g.add((ONT.foundedDate, RDF.type, RDF.Property))
g.add((ONT.country, RDF.type, RDF.Property))

def enrich_with_dbpedia(player_label, player_uri):
    """Fetch additional data from DBpedia for a player"""
    try:
        # Map player names to DBpedia resource names
        name_mappings = {
            "CristianoRonaldo": "Cristiano_Ronaldo",
            "LionelMessi": "Lionel_Messi",
            "KylianMbappe": "Kylian_Mbappé",
            "ErlingHaaland": "Erling_Haaland",
            "NeymarJr": "Neymar",
            "MohamedSalah": "Mohamed_Salah"
        }
        
        dbpedia_name = name_mappings.get(player_label, player_label)
        
        # DBpedia SPARQL endpoint
        sparql_endpoint = "https://dbpedia.org/sparql"
        
        # Query DBpedia for player information
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX dbp: <http://dbpedia.org/property/>
        
        SELECT ?birthDate ?birthPlace ?height ?nationality
        WHERE {{
          dbr:{dbpedia_name} dbo:birthDate ?birthDate .
          OPTIONAL {{ dbr:{dbpedia_name} dbo:birthPlace ?birthPlace }}
          OPTIONAL {{ dbr:{dbpedia_name} dbo:height ?height }}
          OPTIONAL {{ dbr:{dbpedia_name} dbp:nationalteam ?nationality }}
        }}
        LIMIT 1
        """
        
        sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat("json")
        sparql.setTimeout(10)
        results = sparql.query().convert()
        
        if results["results"]["bindings"]:
            result = results["results"]["bindings"][0]
            added_data = []
            
            # Add birth date
            if "birthDate" in result:
                birth_date = result["birthDate"]["value"].split("T")[0]  # Get just the date part
                g.add((player_uri, ONT.birthDate, Literal(birth_date, datatype=XSD.date)))
                added_data.append(f"birthDate: {birth_date}")
            
            # Add birth place as string
            if "birthPlace" in result:
                birth_place_uri = result["birthPlace"]["value"]
                birth_place_name = birth_place_uri.split("/")[-1].replace("_", " ")
                g.add((player_uri, ONT.birthPlace, Literal(birth_place_name, datatype=XSD.string)))
                added_data.append(f"birthPlace: {birth_place_name}")
            
            # Add height
            if "height" in result:
                try:
                    height = float(result["height"]["value"])
                    g.add((player_uri, ONT.height, Literal(height, datatype=XSD.float)))
                    added_data.append(f"height: {height}m")
                except:
                    pass
            
            # Add nationality
            if "nationality" in result:
                nationality = result["nationality"]["value"]
                if isinstance(nationality, str):
                    nat_name = nationality.split("/")[-1].replace("_", " ")
                    g.add((player_uri, ONT.nationality, Literal(nat_name, datatype=XSD.string)))
                    added_data.append(f"nationality: {nat_name}")
            
            if added_data:
                print(f"  ✓ {player_label}: {', '.join(added_data)}")
                return True
        
        print(f"  ✗ {player_label}: No data found in DBpedia")
    except Exception as e:
        print(f"  ✗ {player_label}: Error - {str(e)[:100]}")
    
    return False


print("\n===========================================")
print("ENRICHING DATA FROM DBPEDIA")
print("===========================================\n")

# Select a few high-profile players to enrich with DBpedia data
players_to_enrich = [
    "CristianoRonaldo", "LionelMessi", "KylianMbappe", 
    "ErlingHaaland", "NeymarJr", "MohamedSalah"
]

enriched_count = 0
for player_label in players_to_enrich:
    player_uri = EX[player_label]
    if enrich_with_dbpedia(player_label, player_uri):
        enriched_count += 1

print(f"\n✓ Successfully enriched {enriched_count}/{len(players_to_enrich)} players with DBpedia data")
print(f"Total triples after DBpedia enrichment: {len(g)}")


# ===========================================
# EXTERNAL DATA INTEGRATION - WIKIDATA
# ===========================================

def enrich_with_wikidata(team_label, team_uri):
    """Fetch additional data from Wikidata for a team"""
    try:
        # Wikidata SPARQL endpoint
        sparql_endpoint = "https://query.wikidata.org/sparql"
        
        # Query Wikidata for team information
        query = f"""
        SELECT ?founded ?country ?stadium WHERE {{
          ?team rdfs:label "{team_label}"@en .
          ?team wdt:P31 wd:Q476028 .  # instance of association football club
          OPTIONAL {{ ?team wdt:P571 ?founded }}
          OPTIONAL {{ ?team wdt:P17 ?country }}
          OPTIONAL {{ ?team wdt:P115 ?stadium }}
        }}
        LIMIT 1
        """
        
        sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat("json")
        sparql.addCustomHttpHeader("User-Agent", "KnowledgeGraphBot/1.0")
        results = sparql.query().convert()
        
        if results["results"]["bindings"]:
            result = results["results"]["bindings"][0]
            
            # Add founded date
            if "founded" in result:
                founded = result["founded"]["value"]
                g.add((team_uri, ONT.foundedDate, Literal(founded, datatype=XSD.date)))
                print(f"  Added founded date for {team_label}: {founded}")
            
            # Add country
            if "country" in result:
                country = result["country"]["value"]
                g.add((team_uri, ONT.country, URIRef(country)))
                print(f"  Added country for {team_label}")
            
            return True
    except Exception as e:
        print(f"  Wikidata lookup failed for {team_label}: {e}")
    
    return False


print("\n===========================================")
print("ENRICHING DATA FROM WIKIDATA")
print("===========================================\n")

# Enrich a few teams with Wikidata data
teams_to_enrich = ["Liverpool FC", "Real Madrid", "Manchester City", "Barcelona"]

wikidata_enriched = 0
for team_label in teams_to_enrich:
    # Find the team URI
    team_uri = None
    for t_label, t_uri in teams.items():
        if team_label.replace(" ", "").lower() in t_label.lower():
            team_uri = t_uri
            break
    
    if team_uri:
        print(f"Enriching {team_label} from Wikidata...")
        if enrich_with_wikidata(team_label, team_uri):
            wikidata_enriched += 1

print(f"\n✓ Successfully enriched {wikidata_enriched} teams with Wikidata data")
print(f"Total triples after Wikidata enrichment: {len(g)}")


# ===========================================
# REPORT COUNTS
# ===========================================

player_count = len(list(g.triples((None, RDF.type, ONT.Player))))
team_count = len(list(g.triples((None, RDF.type, ONT.Team))))
match_count = len(list(g.triples((None, RDF.type, ONT.Match))))

print("Triples final:", len(g))
print("Players:", player_count, "Teams:", team_count, "Matches:", match_count)


# ===========================================
# SAVE TTL
# ===========================================

g.serialize(OUTPUT_TTL, format="turtle")
print("Saved:", OUTPUT_TTL)


# ===========================================
# SHACL VALIDATION
# ===========================================

if os.path.exists(SHACL_FILE):
    print("Running SHACL validation...")
    conforms, _, results_text = validate(
        data_graph=g,
        shacl_graph=SHACL_FILE,
        inference='rdfs',
        advanced=True
    )
    print("SHACL conforms:", conforms)
    if not conforms:
        print(results_text)
else:
    print("No SHACL file found.")


# ===========================================
# OPTIONAL REASONING (MOVED UP HERE)
# ===========================================

if OWL_RL_AVAILABLE:
    print("\nRunning OWL-RL reasoning...")
    before = len(g)
    sem = OWLRL_Semantics(g, False, False, False)
    sem.closure()
    sem.flush_stored_triples()
    after = len(g)
    print(f"Triples before: {before}, after reasoning: {after}")
else:
    print("\nOWL-RL not installed.")


# ===========================================
# VALIDATE AND CLEAN GRAPH DATA (AFTER REASONING)
# ===========================================

print("\nValidating graph structure after reasoning...")

# Remove any triples where literals are used as subjects or predicates
invalid_triples = []
for s, p, o in list(g):
    if isinstance(s, Literal):
        invalid_triples.append((s, p, o))
    elif isinstance(p, Literal):
        invalid_triples.append((s, p, o))

print(f"Found {len(invalid_triples)} invalid triples with literals as subjects/predicates")

for triple in invalid_triples:
    g.remove(triple)

print(f"Removed {len(invalid_triples)} invalid triples")
print(f"Triples after cleaning: {len(g)}")
print("Graph validation complete")


# ===========================================
# EXAMPLE SPARQL QUERIES
# ===========================================

def run_and_save(query, csv_name=None):
    res = g.query(query)
    rows = []
    cols = [str(v) for v in res.vars]
    for r in res:
        row = []
        for c in r:
            label = None
            if isinstance(c, URIRef):
                for lbl in g.objects(c, RDFS.label):
                    label = str(lbl)
                    break
                if label:
                    row.append(label)
                else:
                    row.append(c.split("/")[-1])
            else:
                row.append(str(c))
        rows.append(row)
    df = pd.DataFrame(rows, columns=cols)
    # Remove duplicates
    df = df.drop_duplicates()
    print(df)
    if csv_name:
        df.to_csv(csv_name, index=False)
        print("Saved", csv_name)


print("\n--- Total Goals Per Player ---")
q_goals = """
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
"""
run_and_save(q_goals, "total_goals.csv")


print("\n--- Players Per Team ---")
q_players = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT DISTINCT ?playerLabel ?teamLabel
WHERE {
  ?player a ont:Player .
  ?player ont:hasTeam ?team .
  ?player rdfs:label ?playerLabel .
  ?team rdfs:label ?teamLabel .
}
ORDER BY ?teamLabel ?playerLabel
"""
run_and_save(q_players, "players_teams.csv")


print("\n--- Debug: All Liverpool Players ---")
q_debug = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
PREFIX ex: <http://www.semanticSports.org/data/>
SELECT ?player ?hasTeam ?team
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?label .
  FILTER(CONTAINS(?label, "Salah") || CONTAINS(?label, "Diaz") || CONTAINS(?label, "MacAllister"))
  OPTIONAL { ?player ont:hasTeam ?team }
  BIND(EXISTS { ?player ont:hasTeam ?team } AS ?hasTeam)
}
"""
run_and_save(q_debug)


print("\n--- Enriched Player Data from External Sources ---")
q_enriched = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?birthDate ?birthPlace ?height ?nationality
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:birthDate ?birthDate }
  OPTIONAL { ?player ont:birthPlace ?birthPlace }
  OPTIONAL { ?player ont:height ?height }
  OPTIONAL { ?player ont:nationality ?nationality }
  FILTER(BOUND(?birthDate) || BOUND(?birthPlace) || BOUND(?height) || BOUND(?nationality))
}
ORDER BY ?playerLabel
"""
run_and_save(q_enriched, "enriched_players.csv")


print("\n--- Enriched Team Data from External Sources ---")
q_teams_enriched = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel ?foundedDate ?country
WHERE {
  ?team a ont:Team .
  ?team rdfs:label ?teamLabel .
  OPTIONAL { ?team ont:foundedDate ?foundedDate }
  OPTIONAL { ?team ont:country ?country }
  FILTER(BOUND(?foundedDate) || BOUND(?country))
}
ORDER BY ?teamLabel
"""
run_and_save(q_teams_enriched, "enriched_teams.csv")


# ===========================================
# UPLOAD TO FUSEKI
# ===========================================

try:
    print("\nUploading TTL to Fuseki...")
    
    # First, check if Fuseki is running
    base_url = FUSEKI_ENDPOINT.rsplit('/', 2)[0]  # Get base URL
    try:
        ping_response = requests.get(base_url, timeout=5)
        print(f"Fuseki server status: {ping_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Cannot reach Fuseki server at {base_url}")
        print(f"Error: {e}")
        print("Make sure Fuseki is running with: fuseki-server --update --mem /footballKG")
        raise
    
    # Use HTTP POST with N-Triples format (more reliable for Fuseki)
    print("\nConverting to N-Triples format...")
    nt_data = g.serialize(format="nt")
    print(f"Serialized {len(nt_data)} bytes of N-Triples data")
    
    # Debug: Show first few lines of N-Triples
    lines = nt_data.split('\n')
    print(f"Total triples: {len([l for l in lines if l.strip()])}")
    print("\nFirst 5 triples:")
    for i, line in enumerate(lines[:5]):
        if line.strip():
            print(f"  {i+1}: {line[:100]}...")
    
    # Clear existing data first
    print("\nClearing existing data...")
    update_url = FUSEKI_ENDPOINT.replace("/data", "/update")
    clear_query = "CLEAR DEFAULT"
    clear_response = requests.post(
        update_url,
        data=clear_query,
        headers={"Content-Type": "application/sparql-update"}
    )
    print(f"Clear response: {clear_response.status_code}")
    
    # Upload using POST to /data endpoint with N-Triples
    print("\nUploading data...")
    headers = {"Content-Type": "application/n-triples; charset=utf-8"}
    response = requests.post(FUSEKI_ENDPOINT, data=nt_data.encode('utf-8'), headers=headers)
    print(f"Upload response: {response.status_code}")
    
    if response.status_code in [200, 201, 204]:
        print("✓ Upload successful!")
    else:
        print(f"Upload failed: {response.text[:500]}")
        print("\nShowing lines around the error (line 11):")
        for i, line in enumerate(lines[8:15], start=9):
            marker = " <<< ERROR LINE" if i == 11 else ""
            print(f"  Line {i}: {line[:150]}{marker}")
        
        # Try to find any triples with literals as subjects in the actual graph
        print("\nChecking for problematic triples in graph...")
        problem_count = 0
        for s, p, o in list(g):
            if isinstance(s, Literal):
                print(f"  FOUND: Literal as subject: {s} {p} {o}")
                problem_count += 1
                if problem_count >= 5:
                    break
        
        if problem_count == 0:
            print("  No literals as subjects found in graph")
            print("\n  The issue might be in how N-Triples is being serialized.")
            print("  Let's try saving to file instead...")
            
            # Save N-Triples to file for manual inspection
            with open("debug_output.nt", "w", encoding="utf-8") as f:
                f.write(nt_data)
            print("  Saved N-Triples to debug_output.nt for inspection")
        
except Exception as e:
    print(f"Fuseki upload failed with error: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure Fuseki is running: fuseki-server --update --mem /footballKG")
    print("2. Check the dataset name matches: 'footballKG'")
    print("3. Verify the endpoint URL:", FUSEKI_ENDPOINT)
    print("4. Ensure Fuseki allows updates (--update flag)")
    print("5. Try accessing Fuseki UI at: http://localhost:3030")


print("\nPipeline finished.")