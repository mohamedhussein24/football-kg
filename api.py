"""
Flask API for Football Knowledge Graph
Connects React frontend to SPARQL query service
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph, Namespace, RDFS
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Load the knowledge graph
KG_FILE = "football_kg_extended.ttl"
g = Graph()

# Namespaces
ONT = Namespace("http://www.semanticSports.org/ontology#")
EX = Namespace("http://www.semanticSports.org/data/")

print(f"Loading knowledge graph from {KG_FILE}...")
try:
    g.parse(KG_FILE, format="turtle")
    print(f"Knowledge graph loaded successfully with {len(g)} triples.")
except Exception as e:
    print(f"Error loading knowledge graph: {e}")
    g = None


def query_to_json(query_result, query_type="SELECT"):
    """Convert SPARQL query result to JSON format"""
    if query_type == "ASK":
        # ASK queries return a boolean
        return {"answer": bool(query_result.askAnswer)}
    elif query_type == "DESCRIBE" or query_type == "CONSTRUCT":
        # DESCRIBE and CONSTRUCT return a graph
        return {"graph": query_result.serialize(format="turtle")}
    else:
        # SELECT queries return bindings
        if not query_result:
            return {"columns": [], "rows": []}
        
        # Get column names
        columns = [str(v) for v in query_result.vars]
        
        # Get rows
        rows = []
        for row in query_result:
            row_data = []
            for val in row:
                if val is None:
                    row_data.append("")
                    continue
                
                # Try to get label if it's a URI
                if hasattr(val, 'toPython'):
                    val_str = str(val)
                    # Try to get rdfs:label
                    label = None
                    try:
                        for lbl in g.objects(val, RDFS.label):
                            label = str(lbl)
                            break
                    except:
                        pass
                    
                    row_data.append(label if label else val_str)
                else:
                    row_data.append(str(val))
            rows.append(row_data)
        
        return {"columns": columns, "rows": rows}


@app.route('/api/query', methods=['POST'])
def execute_query():
    """Execute a SPARQL query and return results"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Detect query type
        query_upper = query.strip().upper()
        if query_upper.startswith('ASK'):
            query_type = "ASK"
        elif query_upper.startswith('DESCRIBE'):
            query_type = "DESCRIBE"
        elif query_upper.startswith('CONSTRUCT'):
            query_type = "CONSTRUCT"
        else:
            query_type = "SELECT"
        
        # Execute query
        result = g.query(query)
        
        # Convert to JSON based on query type
        json_result = query_to_json(result, query_type)
        
        return jsonify(json_result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players with their teams and goal statistics"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?playerLabel ?teamLabel (SUM(?g) AS ?totalGoals)
        WHERE {
          ?player a ont:Player .
          ?player rdfs:label ?playerLabel .
          OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
          OPTIONAL { ?player ont:hasPerformance ?p . ?p ont:scoredGoals ?g . }
        }
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?totalGoals)
        """
        
        result = g.query(query)
        players = []
        
        for row in result:
            player = {
                "playerLabel": str(row[0]) if row[0] else "",
                "teamLabel": str(row[1]) if row[1] else "N/A",
                "totalGoals": int(row[2]) if row[2] else 0
            }
            players.append(player)
        
        return jsonify(players)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get all teams with player counts and total goals"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?teamLabel (COUNT(DISTINCT ?player) AS ?playerCount) (SUM(?g) AS ?totalGoals)
        WHERE {
          ?team a ont:Team .
          ?team rdfs:label ?teamLabel .
          OPTIONAL { ?player ont:hasTeam ?team . }
          OPTIONAL { ?player ont:hasPerformance ?p . ?p ont:scoredGoals ?g . }
        }
        GROUP BY ?teamLabel
        ORDER BY ?teamLabel
        """
        
        result = g.query(query)
        teams = []
        
        for row in result:
            team = {
                "teamLabel": str(row[0]) if row[0] else "",
                "playerCount": int(row[1]) if row[1] else 0,
                "totalGoals": int(row[2]) if row[2] else 0
            }
            teams.append(team)
        
        return jsonify(teams)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "graph_loaded": g is not None,
        "triples": len(g) if g else 0
    })


@app.route('/api/query/dbpedia', methods=['POST'])
def query_dbpedia():
    """Execute a federated SPARQL query against DBpedia"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # DBpedia SPARQL endpoint
        sparql = SPARQLWrapper("https://dbpedia.org/sparql")
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(30)
        
        results = sparql.query().convert()
        
        # Convert DBpedia results to our format
        if "results" in results and "bindings" in results["results"]:
            bindings = results["results"]["bindings"]
            if not bindings:
                return jsonify({"columns": [], "rows": [], "source": "DBpedia"})
            
            # Get column names from first result
            columns = list(bindings[0].keys())
            rows = []
            
            for binding in bindings:
                row = []
                for col in columns:
                    if col in binding:
                        value = binding[col]["value"]
                        # Extract readable name from URI if needed
                        if isinstance(value, str) and value.startswith("http://"):
                            if "dbpedia.org/resource/" in value:
                                value = value.split("/")[-1].replace("_", " ")
                            elif "dbpedia.org/ontology/" in value:
                                value = value.split("/")[-1]
                            elif "dbpedia.org/property/" in value:
                                value = value.split("/")[-1]
                        # Handle dates
                        elif isinstance(value, str) and "T" in value and value.startswith("19") or value.startswith("20"):
                            value = value.split("T")[0]
                        row.append(value)
                    else:
                        row.append("")
                rows.append(row)
            
            return jsonify({
                "columns": columns, 
                "rows": rows,
                "source": "DBpedia",
                "sourceUrl": "https://dbpedia.org"
            })
        else:
            return jsonify({"error": "Unexpected DBpedia response format"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/query/wikidata', methods=['POST'])
def query_wikidata():
    """Execute a SPARQL query against Wikidata"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Wikidata SPARQL endpoint
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(30)
        
        results = sparql.query().convert()
        
        # Convert Wikidata results to our format
        if "results" in results and "bindings" in results["results"]:
            bindings = results["results"]["bindings"]
            if not bindings:
                return jsonify({"columns": [], "rows": [], "source": "Wikidata"})
            
            # Get column names from first result
            columns = list(bindings[0].keys())
            rows = []
            
            for binding in bindings:
                row = []
                for col in columns:
                    if col in binding:
                        value = binding[col]["value"]
                        # Clean up Wikidata URIs
                        if isinstance(value, str) and value.startswith("http://www.wikidata.org/"):
                            value = value.split("/")[-1]
                        row.append(value)
                    else:
                        row.append("")
                rows.append(row)
            
            return jsonify({
                "columns": columns, 
                "rows": rows,
                "source": "Wikidata",
                "sourceUrl": "https://www.wikidata.org"
            })
        else:
            return jsonify({"error": "Unexpected Wikidata response format"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/query/federated', methods=['POST'])
def query_federated():
    """Execute a federated query combining local graph and DBpedia"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Execute against local graph first
        local_result = g.query(query)
        
        # For federated queries, we'll need SERVICE clause in SPARQL
        # This is a simplified version - full federated queries require SERVICE
        json_result = query_to_json(local_result, "SELECT")
        
        return jsonify(json_result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/players/stats', methods=['GET'])
def get_player_stats():
    """Get detailed player statistics with visualizations"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?playerLabel ?teamLabel 
               (COALESCE(SUM(?goals), 0) AS ?totalGoals) 
               (COALESCE(SUM(?assists), 0) AS ?totalAssists)
               (COALESCE(AVG(?rating), 0) AS ?avgRating)
               (COUNT(DISTINCT ?perf) AS ?matchCount)
        WHERE {
          ?player a ont:Player .
          ?player rdfs:label ?playerLabel .
          OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
          OPTIONAL { 
            ?player ont:hasPerformance ?perf .
            OPTIONAL { ?perf ont:scoredGoals ?goals }
            OPTIONAL { ?perf ont:madeAssists ?assists }
            OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
          }
        }
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?totalGoals)
        LIMIT 20
        """
        
        result = g.query(query)
        players = []
        
        for row in result:
            player = {
                "playerLabel": str(row[0]) if row[0] else "",
                "teamLabel": str(row[1]) if row[1] else "N/A",
                "totalGoals": int(row[2]) if row[2] else 0,
                "totalAssists": int(row[3]) if row[3] else 0,
                "avgRating": round(float(row[4]), 2) if row[4] else 0,
                "matchCount": int(row[5]) if row[5] else 0
            }
            players.append(player)
        
        return jsonify(players)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/teams/comparison', methods=['GET'])
def get_team_comparison():
    """Get team comparison data for visualization"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?teamLabel 
               (COUNT(DISTINCT ?player) AS ?playerCount) 
               (COALESCE(SUM(?goals), 0) AS ?totalGoals)
               (COALESCE(AVG(?goals), 0) AS ?avgGoalsPerPlayer)
               (COALESCE(MAX(?goals), 0) AS ?topScorerGoals)
        WHERE {
          ?team a ont:Team .
          ?team rdfs:label ?teamLabel .
          OPTIONAL { ?player ont:hasTeam ?team . }
          OPTIONAL { 
            ?player ont:hasPerformance ?p .
            ?p ont:scoredGoals ?goals .
          }
        }
        GROUP BY ?teamLabel
        ORDER BY DESC(?totalGoals)
        """
        
        result = g.query(query)
        teams = []
        
        for row in result:
            team = {
                "teamLabel": str(row[0]) if row[0] else "",
                "playerCount": int(row[1]) if row[1] else 0,
                "totalGoals": int(row[2]) if row[2] else 0,
                "avgGoalsPerPlayer": round(float(row[3]), 2) if row[3] else 0,
                "topScorerGoals": int(row[4]) if row[4] else 0
            }
            teams.append(team)
        
        return jsonify(teams)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze/player', methods=['POST'])
def analyze_player():
    """Comprehensive player analysis combining local KG and external data"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        data = request.get_json()
        player_name = data.get('playerName', '').strip()
        
        if not player_name:
            return jsonify({"error": "Player name required"}), 400
        
        # Step 1: Get local KG data
        # Escape single quotes and prepare name for SPARQL
        safe_name = player_name.replace("'", "''").replace('"', '\\"')
        local_query = f"""
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?playerLabel ?teamLabel ?positionLabel 
               (COALESCE(SUM(?goals), 0) AS ?totalGoals)
               (COALESCE(SUM(?assists), 0) AS ?totalAssists)
               (COALESCE(AVG(?rating), 0) AS ?avgRating)
               (COUNT(?perf) AS ?matchCount)
               (MIN(?goals) AS ?minGoals)
               (MAX(?goals) AS ?maxGoals)
               (AVG(?goals) AS ?avgGoalsPerMatch)
        WHERE {{
          ?player a ont:Player .
          ?player rdfs:label ?playerLabel .
          FILTER(CONTAINS(LCASE(STR(?playerLabel)), LCASE(STR("{safe_name}"))) || CONTAINS(LCASE(STR(?playerLabel)), LCASE(STR("{safe_name.replace(' ', '')}"))))
          OPTIONAL {{ ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }}
          OPTIONAL {{ ?player ont:hasPosition ?position . ?position rdfs:label ?positionLabel . }}
          OPTIONAL {{
            ?player ont:hasPerformance ?perf .
            OPTIONAL {{ ?perf ont:scoredGoals ?goals }}
            OPTIONAL {{ ?perf ont:madeAssists ?assists }}
            OPTIONAL {{ ?perf ont:hasPerformanceRating ?rating }}
          }}
        }}
        GROUP BY ?playerLabel ?teamLabel ?positionLabel
        ORDER BY ASC(STRLEN(STR(?playerLabel)))
        LIMIT 1
        """
        
        local_result = g.query(local_query)
        local_data = None
        
        # Filter by player name in Python (case-insensitive)
        player_name_lower = player_name.lower()
        # Use the first result (we limited to 1 in SPARQL)
        for row in local_result:
            row_player_name = str(row[0]) if row[0] else ""
            if True: # We trust the SPARQL query to return the best match
                local_data = {
                    "playerLabel": row_player_name,
                    "teamLabel": str(row[1]) if row[1] else None,
                    "positionLabel": str(row[2]) if row[2] else None,
                    "totalGoals": int(row[3]) if row[3] else 0,
                    "totalAssists": int(row[4]) if row[4] else 0,
                    "avgRating": float(row[5]) if row[5] else 0,
                    "matchCount": int(row[6]) if row[6] else 0,
                    "minGoals": int(row[7]) if row[7] else 0,
                    "maxGoals": int(row[8]) if row[8] else 0,
                    "avgGoalsPerMatch": float(row[9]) if row[9] else 0
                }
                break
        
        if not local_data:
            return jsonify({"error": f"Player '{player_name}' not found in knowledge graph"}), 404
        
        # Step 2: Try to enrich with TheSportsDB
        real_world_data = {}
        career_highlight = None
        
        try:
            # Search by name
            tsdb_url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={player_name}"
            tsdb_res = requests.get(tsdb_url, timeout=5)
            
            if tsdb_res.status_code == 200:
                tsdb_json = tsdb_res.json()
                if tsdb_json.get("player"):
                    # Get the most relevant result
                    player_data = tsdb_json["player"][0]
                    real_world_data = {
                        "realName": player_data.get("strPlayer"),
                        "realTeam": player_data.get("strTeam"),
                        "realNationality": player_data.get("strNationality"),
                        "birthDate": player_data.get("dateBorn"),
                        "height": player_data.get("strHeight"),
                        "weight": player_data.get("strWeight"),
                        "thumb": player_data.get("strThumb"),
                        "cutout": player_data.get("strCutout"),
                        "description": player_data.get("strDescriptionEN"),
                        "position": player_data.get("strPosition"),
                        "facebook": player_data.get("strFacebook"),
                        "twitter": player_data.get("strTwitter"),
                        "instagram": player_data.get("strInstagram")
                    }
                    
                    # Extract Career Highlight from description
                    description = player_data.get("strDescriptionEN", "")
                    if description:
                        # Look for sentences with keywords
                        sentences = description.split('.')
                        for sentence in sentences:
                            s_lower = sentence.lower()
                            if "won" in s_lower or "champion" in s_lower or "award" in s_lower or "record" in s_lower:
                                career_highlight = sentence.strip() + "."
                                break
                        if not career_highlight and len(sentences) > 0:
                             career_highlight = sentences[0].strip() + "."
                             
        except Exception as e:
            print(f"TheSportsDB enrichment failed: {e}")
        
        # Step 3: Calculate statistics and insights
        stats = {
            "totalGoals": local_data["totalGoals"],
            "totalAssists": local_data["totalAssists"],
            "avgRating": local_data["avgRating"],
            "consistency": min(100, (local_data["matchCount"] * 10) + (local_data["avgGoalsPerMatch"] * 20)) if local_data["matchCount"] > 0 else 0,
            "teamImpact": min(100, ((local_data["totalGoals"] + local_data["totalAssists"]) * 2))
        }
        
        # Generate insights (Removed "Limited match data" warning)
        insights = []
        if local_data["totalGoals"] > 20:
            insights.append({"type": "strength", "text": f"High goal-scoring ability with {local_data['totalGoals']} goals"})
        if local_data["totalAssists"] > 10:
            insights.append({"type": "strength", "text": f"Strong playmaking skills with {local_data['totalAssists']} assists"})
        if local_data["avgRating"] > 7.5:
            insights.append({"type": "strength", "text": f"Consistently high performance rating of {local_data['avgRating']:.2f}"})
        
        # Step 4: Find similar players (improved logic)
        similar_result = g.query(local_query)
        similar_players = []
        
        # Get current player's canonical label for filtering
        current_player_label = local_data.get("playerLabel", "").lower()

        for row in similar_result:
            row_player_name = str(row[0]) if row[0] else ""
            
            # Skip the current player (robust check)
            if row_player_name.lower() == current_player_label:
                continue
            goals = int(row[3]) if row[3] else 0
            assists = int(row[4]) if row[4] else 0
            rating = float(row[5]) if row[5] else 0
            
            # Only include players with some performance data
            if goals == 0 and assists == 0:
                continue
            
            # Calculate similarity score (weighted to vary results)
            # Normalize diffs slightly to avoid exact match bias for small numbers
            goal_diff = abs(goals - local_data["totalGoals"])
            assist_diff = abs(assists - local_data["totalAssists"])
            rating_diff = abs(rating - local_data["avgRating"])
            
            # Add a small random factor to break ties and add variety
            # (In production, use more attributes like Position)
            
            similarity = max(0, 100 - (goal_diff * 1.5) - (assist_diff * 2.5) - (rating_diff * 8))
            
            similar_players.append({
                "playerLabel": row_player_name,
                "totalGoals": goals,
                "totalAssists": assists,
                "avgRating": rating,
                "similarity": int(similarity)
            })
        
        # Sort by similarity and limit
        similar_players.sort(key=lambda x: x["similarity"], reverse=True)
        similar_players = similar_players[:5] # Limit to 5 for better UI focus
        
        # Step 5: Generate recommendations (with dynamic Team Fit)
        recommendations = generate_recommendations(local_data, stats, similar_players)
        
        # Data Sources Attribution
        data_sources_map = {
            "name": "Local KG",
            "team": "Local KG",
            "position": "Local KG",
            "goals": "Local KG",
            "assists": "Local KG",
            "rating": "Local KG",
            "matches": "Local KG",
            "bio": "TheSportsDB" if real_world_data else "N/A",
            "image": "TheSportsDB" if real_world_data else "N/A",
            "nationality": "TheSportsDB" if real_world_data else "N/A",
            "birthDate": "TheSportsDB" if real_world_data else "N/A",
            "height": "TheSportsDB" if real_world_data else "N/A"
        }
        
        # Merge data (Prioritize Real World for display fields if Local is missing/generic)
        final_data = {
            **local_data,
            **real_world_data,
            "careerHighlight": career_highlight,
            "stats": stats,
            "insights": insights,
            "dataSources": ["Local KG", "TheSportsDB"] if real_world_data else ["Local KG"],
            "sourceMap": data_sources_map
        }
        
        return jsonify({
            "analysis": final_data,
            "recommendations": recommendations
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/query/integrated', methods=['POST'])
def integrated_query():
    """Execute 'Smart Queries' that combine Local KG and TheSportsDB"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
        
    try:
        data = request.get_json()
        query_type = data.get('type')
        
        # Helper to format name: "ErlingHaaland" -> "Erling Haaland"
        def format_name_for_search(name):
            import re
            # Insert space before capital letters (except the first one)
            return re.sub(r'(?<!^)(?=[A-Z])', ' ', name).strip()
        
        if query_type == "top_scorers_enriched":
            # 1. Get Top Scorers from Local KG
            local_sparql = """
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
            LIMIT 8
            """
            
            results = g.query(local_sparql)
            enriched_rows = []
            
            for row in results:
                name_raw = str(row[0])
                goals = str(row[1])
                search_name = format_name_for_search(name_raw)
                
                # 2. Enrich with TheSportsDB (Nationality, Team)
                nationality = "Unknown"
                real_team = "Unknown"
                
                try:
                    tsdb_url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php"
                    res = requests.get(tsdb_url, params={'p': search_name}, timeout=2)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("player"):
                            # Find exact match or take first
                            p_data = data["player"][0]
                            nationality = p_data.get("strNationality", "Unknown")
                            real_team = p_data.get("strTeam", "Unknown")
                except:
                    pass
                
                enriched_rows.append([name_raw, goals, nationality, real_team])
            
            return jsonify({
                "columns": ["Player Name", "Total Goals (Local KG)", "Nationality (TheSportsDB)", "Current Team (TheSportsDB)"],
                "rows": enriched_rows,
                "source": "Integrated (Local KG + TheSportsDB)"
            })
            
        elif query_type == "young_talents":
            # 1. Get High Potential Players (Rating > 7.0)
            local_sparql = """
            PREFIX ont: <http://www.semanticSports.org/ontology#>
            SELECT ?playerLabel (AVG(?rating) AS ?avgRating)
            WHERE {
              ?player a ont:Player .
              ?player rdfs:label ?playerLabel .
              ?player ont:hasPerformance ?p .
              ?p ont:hasPerformanceRating ?rating .
            }
            GROUP BY ?playerLabel
            HAVING (AVG(?rating) > 7.0)
            LIMIT 15
            """
            
            results = g.query(local_sparql)
            young_talents = []
            from datetime import datetime
            
            for row in results:
                name_raw = str(row[0])
                rating = f"{float(row[1]):.2f}"
                search_name = format_name_for_search(name_raw)
                
                # 2. Check Age via TheSportsDB
                age = "Unknown"
                birth_date = "Unknown"
                
                try:
                    tsdb_url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php"
                    res = requests.get(tsdb_url, params={'p': search_name}, timeout=2)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("player"):
                            p_data = data["player"][0]
                            dob_str = p_data.get("dateBorn")
                            if dob_str:
                                birth_date = dob_str
                                dob = datetime.strptime(dob_str, "%Y-%m-%d")
                                today = datetime.today()
                                age_val = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                                age = str(age_val)
                                
                                # Filter: Only include if under 25 (Young Talent)
                                if age_val < 25:
                                    young_talents.append([name_raw, rating, age, birth_date])
                except:
                    pass
            
            return jsonify({
                "columns": ["Player Name", "Avg Rating (Local KG)", "Age (Calc from TheSportsDB)", "Birth Date (TheSportsDB)"],
                "rows": young_talents,
                "source": "Integrated (Local KG + TheSportsDB)"
            })
            
        elif query_type == "physicality_analysis":
            # 1. Get High Scoring Players
            local_sparql = """
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
            LIMIT 12
            """
            results = g.query(local_sparql)
            rows = []
            
            for res_row in results:
                name_raw = str(res_row[0])
                goals = str(res_row[1])
                search_name = format_name_for_search(name_raw)
                
                height = "Unknown"
                weight = "Unknown"
                
                try:
                    tsdb_url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php"
                    resp = requests.get(tsdb_url, params={'p': search_name}, timeout=2)
                    if resp.status_code == 200:
                        d = resp.json()
                        if d.get("player"):
                            p = d["player"][0]
                            height = p.get("strHeight", "Unknown")
                            weight = p.get("strWeight", "Unknown")
                except:
                    pass
                
                rows.append([name_raw, goals, height, weight])
                
            return jsonify({
                "columns": ["Player", "Total Goals (Local)", "Height (External)", "Weight (External)"],
                "rows": rows,
                "source": "Integrated (Local KG + TheSportsDB)"
            })

        elif query_type == "club_country":
            # 1. Get Player and Team
            local_sparql = """
            PREFIX ont: <http://www.semanticSports.org/ontology#>
            SELECT ?playerLabel ?teamLabel
            WHERE {
              ?player a ont:Player .
              ?player rdfs:label ?playerLabel .
              ?player ont:hasTeam ?team .
              ?team rdfs:label ?teamLabel .
            }
            LIMIT 12
            """
            results = g.query(local_sparql)
            rows = []
            
            for res_row in results:
                name_raw = str(res_row[0])
                club = str(res_row[1])
                search_name = format_name_for_search(name_raw)
                
                nationality = "Unknown"
                desc_snippet = "No description available."
                
                try:
                    tsdb_url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php"
                    resp = requests.get(tsdb_url, params={'p': search_name}, timeout=2)
                    if resp.status_code == 200:
                        d = resp.json()
                        if d.get("player"):
                            p = d["player"][0]
                            nationality = p.get("strNationality", "Unknown")
                            desc = p.get("strDescriptionEN", "")
                            if desc:
                                desc_snippet = desc[:50] + "..."
                except:
                    pass
                
                rows.append([name_raw, club, nationality, desc_snippet])
                
            return jsonify({
                "columns": ["Player", "Club (Local)", "Nationality (External)", "Bio Snippet (External)"],
                "rows": rows,
                "source": "Integrated (Local KG + TheSportsDB)"
            })
            
        elif query_type == "player_awards":
            # 1. Get Top Scorers for Awards Search
            local_sparql = """
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
            LIMIT 5
            """
            results = g.query(local_sparql)
            rows = []
            
            for res_row in results:
                name_raw = str(res_row[0])
                goals = str(res_row[1])
                search_name = format_name_for_search(name_raw)
                
                award_count = "Unknown"
                
                try:
                    # SPARQL Query to Wikidata for awards (P166) count for player
                    wd_sparql = f"""
                    SELECT (COUNT(?award) AS ?count) WHERE {{
                      ?player rdfs:label "{search_name}"@en .
                      ?player wdt:P106 wd:Q937857 .
                      ?player wdt:P166 ?award .
                    }}
                    """
                    wd_url = "https://query.wikidata.org/sparql"
                    wd_res = requests.get(wd_url, params={'query': wd_sparql, 'format': 'json'}, 
                                          headers={'User-Agent': 'FootballKG/1.0'}, timeout=5)
                    
                    if wd_res.status_code == 200:
                        d = wd_res.json()
                        if d.get("results", {}).get("bindings"):
                             award_count = d["results"]["bindings"][0]["count"]["value"]
                except:
                    pass
                
                rows.append([name_raw, goals, award_count])
                
            return jsonify({
                "columns": ["Player", "Goals (Local)", "Awards Count (Wikidata)"],
                "rows": rows,
                "source": "Integrated (Local KG + Wikidata)"
            })
            
        else:
            return jsonify({"error": "Unknown query type"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_recommendations(player_data, stats, similar_players):
    """Generate recommendations based on player stats and similar players"""
    
    # 1. Best Position
    recommendations = {}
    best_position = "Midfielder"
    reason = "Balanced stats suggest meaningful contribution in midfield."
    
    goals = player_data["totalGoals"]
    assists = player_data["totalAssists"]
    
    if goals > assists * 1.5:
        best_position = "Forward/Striker"
        reason = "High goal-to-assist ratio indicates strong finishing ability."
    elif assists > goals * 1.2:
        best_position = "Attacking Midfielder/Playmaker"
        reason = "Higher assist count suggests strong vision and passing."
    elif stats["avgRating"] > 8.0:
        best_position = "Key Playmaker"
        reason = "Exceptional rating indicates ability to control the game."
        
    recommendations["bestPosition"] = best_position
    recommendations["positionReason"] = reason

    # 2. Team Fit Analysis (Dynamic based on team playstyle)
    # Define simple playstyles for demo purposes
    team_styles = {
        "RealMadrid": {"style": "Counter-Attack", "needs": "goals"},
        "ManchesterCity": {"style": "Possession", "needs": "passing"},
        "LiverpoolFC": {"style": "High Press", "needs": "workrate"},
        "BayernMunich": {"style": "Direct", "needs": "goals"},
        "Barcelona": {"style": "Tiki-Taka", "needs": "passing"},
        "PSG": {"style": "Star Power", "needs": "rating"}
    }
    
    team_fit = []
    for team, profile in team_styles.items():
        base_score = 60 # Base fit
        fit_reason = "Standard roster fit."
        
        if profile["needs"] == "goals":
            if goals > 20: 
                base_score += 30
                fit_reason = "Excellent fit for high-scoring attack."
            elif goals > 10:
                base_score += 15
                fit_reason = "Good scoring depth addition."
            else:
                base_score -= 10
                fit_reason = "Might struggle to meet scoring demands."
                
        elif profile["needs"] == "passing":
            if assists > 15:
                base_score += 30
                fit_reason = "Perfect for possession-based system."
            elif assists > 8:
                base_score += 20
                fit_reason = "Strong passer, fits the system."
            else:
                base_score -= 5
                fit_reason = "Passing stats slightly below system average."
                
        elif profile["needs"] == "rating":
            if stats["avgRating"] > 7.5:
                base_score += 35
                fit_reason = "Elite performer matches star-studded squad."
            else:
                base_score += 5
                fit_reason = "Solid addition to the squad."
                
        # Randomize slightly for variety if scores are identical
        import random
        base_score += random.randint(-5, 5)
        
        # Cap score
        final_score = min(98, max(40, base_score))
        
        team_fit.append({
            "team": team,
            "score": final_score,
            "reason": fit_reason
        })
    
    # Sort by score
    team_fit.sort(key=lambda x: x["score"], reverse=True)
    recommendations["teamFit"] = team_fit[:3] # Top 3 fits
    
    # Similar players
    if similar_players:
        recommendations["similarPlayers"] = similar_players[:5]
    
    # Improvement areas
    improvements = []
    if player_data["totalAssists"] < 5 and player_data["totalGoals"] > 10:
        improvements.append({
            "area": "Playmaking",
            "suggestion": "Focus on creating opportunities for teammates to increase assist count"
        })
    if player_data["avgRating"] < 7.0:
        improvements.append({
            "area": "Consistency",
            "suggestion": "Work on maintaining consistent performance levels across matches"
        })
    if player_data["matchCount"] < 10:
        improvements.append({
            "area": "Match Experience",
            "suggestion": "More match time needed to fully assess potential"
        })
    
    recommendations["improvementAreas"] = improvements
    
    # Career trajectory
    if stats["consistency"] > 70 and stats["teamImpact"] > 60:
        recommendations["careerTrajectory"] = "Player shows strong upward trajectory with consistent high performance. Potential for elite-level contribution."
    elif stats["consistency"] > 50:
        recommendations["careerTrajectory"] = "Solid performance foundation with room for growth. Continued development recommended."
    else:
        recommendations["careerTrajectory"] = "Early stage player with potential. Focus on consistent performance and skill development."
    
    return recommendations


@app.route('/api/external/openligadb/matches', methods=['GET'])
def get_openligadb_matches():
    """Get matches from OpenLigaDB (free, no API key required)"""
    try:
        league = request.args.get('league', 'bl1')  # bl1 = Bundesliga
        season = request.args.get('season', '2024')
        
        response = requests.get(
            f'https://api.openligadb.de/getmatchdata/{league}/{season}',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "data": data[:20] if isinstance(data, list) else data,
                "source": "OpenLigaDB",
                "sourceUrl": "https://www.openligadb.de/",
                "note": "Free German football database - no API key required"
            })
        else:
            return jsonify({
                "error": f"API returned status {response.status_code}",
                "source": "OpenLigaDB"
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "source": "OpenLigaDB"
        }), 500

@app.route('/api/real/search', methods=['GET'])
def search_thesportsdb():
    """Proxy for TheSportsDB search"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Query required"}), 400
            
        # TheSportsDB free API key is '3'
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={query}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch from TheSportsDB"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/real/player/<id>', methods=['GET'])
def get_thesportsdb_player(id):
    """Get specific player details from TheSportsDB"""
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/lookupplayer.php?id={id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Failed to fetch from TheSportsDB"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/external/football-api/leagues', methods=['GET'])
def get_football_api_leagues():
    """Get leagues info (demo endpoint - requires API key)"""
    return jsonify({
        "message": "This endpoint requires API-Football API key",
        "source": "API-Football",
        "sourceUrl": "https://www.api-football.com/",
        "note": "Register at https://www.api-football.com/ to get free API key",
        "example": {
            "endpoint": "/api/external/openligadb/matches",
            "description": "Try OpenLigaDB endpoint which is free and doesn't require API key"
        }
    })


@app.route('/api/external/enriched-players', methods=['GET'])
def get_enriched_players():
    """Get players enriched with external data from DBpedia"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?playerLabel ?teamLabel 
               (COALESCE(SUM(?goals), 0) AS ?totalGoals)
               (COALESCE(SUM(?assists), 0) AS ?totalAssists)
               (COALESCE(AVG(?rating), 0) AS ?avgRating)
        WHERE {
          ?player a ont:Player .
          ?player rdfs:label ?playerLabel .
          OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
          OPTIONAL {
            ?player ont:hasPerformance ?perf .
            OPTIONAL { ?perf ont:scoredGoals ?goals }
            OPTIONAL { ?perf ont:madeAssists ?assists }
            OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
          }
        }
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?totalGoals)
        LIMIT 15
        """
        
        result = g.query(query)
        players = []
        
        for row in result:
            player_name = str(row[0])
            team = str(row[1]) if row[1] else None
            goals = int(row[2]) if row[2] else 0
            assists = int(row[3]) if row[3] else 0
            rating = float(row[4]) if row[4] else 0
            
            dbpedia_mapping = {
                'Cristiano Ronaldo': 'Cristiano_Ronaldo',
                'Lionel Messi': 'Lionel_Messi',
                'Kylian Mbappe': 'Kylian_Mbappé',
                'Erling Haaland': 'Erling_Haaland'
            }
            dbpedia_name = dbpedia_mapping.get(player_name, player_name.replace(' ', '_'))
            
            enriched_data = {
                "playerLabel": player_name,
                "teamLabel": team,
                "totalGoals": goals,
                "totalAssists": assists,
                "avgRating": rating,
                "dataSources": ["Local KG"]
            }
            
            try:
                dbpedia_query = f"""
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX dbr: <http://dbpedia.org/resource/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                
                SELECT ?birthDate ?birthPlace ?height ?nationality
                WHERE {{
                  dbr:{dbpedia_name} rdfs:label ?label .
                  FILTER(LANG(?label) = "en")
                  OPTIONAL {{ dbr:{dbpedia_name} dbo:birthDate ?birthDate }}
                  OPTIONAL {{ dbr:{dbpedia_name} dbo:birthPlace ?birthPlace }}
                  OPTIONAL {{ dbr:{dbpedia_name} dbo:height ?height }}
                  OPTIONAL {{ dbr:{dbpedia_name} dbo:nationality ?nationality }}
                }}
                LIMIT 1
                """
                
                sparql = SPARQLWrapper("https://dbpedia.org/sparql")
                sparql.setQuery(dbpedia_query)
                sparql.setReturnFormat(JSON)
                sparql.setTimeout(10)
                
                dbpedia_result = sparql.query().convert()
                if "results" in dbpedia_result and "bindings" in dbpedia_result["results"]:
                    bindings = dbpedia_result["results"]["bindings"]
                    if bindings:
                        binding = bindings[0]
                        enriched_data["birthDate"] = binding.get("birthDate", {}).get("value", "").split("T")[0] if "birthDate" in binding else None
                        enriched_data["birthPlace"] = binding.get("birthPlace", {}).get("value", "").split("/")[-1].replace("_", " ") if "birthPlace" in binding else None
                        enriched_data["height"] = binding.get("height", {}).get("value", "") if "height" in binding else None
                        enriched_data["nationality"] = binding.get("nationality", {}).get("value", "").split("/")[-1].replace("_", " ") if "nationality" in binding else None
                        enriched_data["dataSources"].append("DBpedia")
            except:
                pass
            
            performance_score = (goals * 2) + (assists * 1.5) + (rating * 5)
            estimated_value = max(5, min(200, int(performance_score * 0.5)))
            enriched_data["estimatedValue"] = estimated_value
            enriched_data["dataSources"].append("Market Estimate")
            
            players.append(enriched_data)
        
        return jsonify({"players": players})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/external/team-comparison', methods=['GET'])
def get_external_team_comparison():
    """Compare teams using local and external data"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?teamLabel 
               (COUNT(DISTINCT ?player) AS ?playerCount)
               (COALESCE(SUM(?goals), 0) AS ?localGoals)
        WHERE {
          ?team a ont:Team .
          ?team rdfs:label ?teamLabel .
          OPTIONAL { ?player ont:hasTeam ?team }
          OPTIONAL {
            ?player ont:hasPerformance ?p .
            ?p ont:scoredGoals ?goals .
          }
        }
        GROUP BY ?teamLabel
        ORDER BY DESC(?localGoals)
        LIMIT 10
        """
        
        result = g.query(query)
        teams = []
        
        for row in result:
            team_name = str(row[0])
            player_count = int(row[1]) if row[1] else 0
            local_goals = int(row[2]) if row[2] else 0
            
            external_rating = min(100, (local_goals * 2) + (player_count * 5))
            
            teams.append({
                "teamLabel": team_name,
                "playerCount": player_count,
                "localGoals": local_goals,
                "externalRating": int(external_rating),
                "dataSources": ["Local KG", "External Rating Estimate"]
            })
        
        return jsonify({"teams": teams})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/external/market-analysis', methods=['GET'])
def get_market_analysis():
    """Market value analysis based on performance"""
    if not g:
        return jsonify({"error": "Knowledge graph not loaded"}), 500
    
    try:
        query = """
        PREFIX ont: <http://www.semanticSports.org/ontology#>
        SELECT ?playerLabel 
               (COALESCE(SUM(?goals), 0) AS ?totalGoals)
               (COALESCE(SUM(?assists), 0) AS ?totalAssists)
               (COALESCE(AVG(?rating), 0) AS ?avgRating)
               (COUNT(?perf) AS ?matches)
        WHERE {
          ?player a ont:Player .
          ?player rdfs:label ?playerLabel .
          OPTIONAL {
            ?player ont:hasPerformance ?perf .
            OPTIONAL { ?perf ont:scoredGoals ?goals }
            OPTIONAL { ?perf ont:madeAssists ?assists }
            OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
          }
        }
        GROUP BY ?playerLabel
        ORDER BY DESC(?totalGoals)
        LIMIT 20
        """
        
        result = g.query(query)
        players = []
        
        for row in result:
            player_name = str(row[0])
            goals = int(row[1]) if row[1] else 0
            assists = int(row[2]) if row[2] else 0
            rating = float(row[3]) if row[3] else 0
            matches = int(row[4]) if row[4] else 0
            
            performance_score = (goals * 2) + (assists * 1.5) + (rating * 5) + (matches * 0.5)
            estimated_value = max(5, min(200, int(performance_score * 0.5)))
            
            if estimated_value > 100:
                recommendation = "Elite player - High market value"
            elif estimated_value > 50:
                recommendation = "Strong performer - Good investment"
            elif estimated_value > 20:
                recommendation = "Solid player - Moderate value"
            else:
                recommendation = "Developing player - Potential value"
            
            players.append({
                "playerLabel": player_name,
                "totalGoals": goals,
                "totalAssists": assists,
                "avgRating": rating,
                "matches": matches,
                "performanceScore": int(performance_score),
                "estimatedValue": estimated_value,
                "recommendation": recommendation
            })
        
        return jsonify({"players": players})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/external/news', methods=['GET'])
def get_news():
    """Get latest football news (simulated from external sources)"""
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        news_items = [
            {
                "title": "Transfer Window Analysis: Top Performers Attract Interest",
                "date": today,
                "content": "Based on performance data from the knowledge graph, several top-scoring players are attracting attention from major clubs. Market analysis suggests strong transfer activity.",
                "source": "Football Analytics",
                "link": "https://example.com/news1"
            },
            {
                "title": "Team Performance Review: Goals and Assists Breakdown",
                "date": today,
                "content": "Comprehensive analysis of team performances combining local match data with external ratings. Several teams showing strong offensive capabilities.",
                "source": "Sports Data Hub",
                "link": "https://example.com/news2"
            },
            {
                "title": "Player Market Values: Performance-Based Estimates",
                "date": today,
                "content": "Market value estimates calculated from performance metrics show significant variations. Top performers command premium valuations.",
                "source": "Transfer Market Insights",
                "link": "https://example.com/news3"
            }
        ]
        
        return jsonify({"news": news_items})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)

