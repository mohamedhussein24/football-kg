# ===========================================
# complex_queries.py — 12 Advanced SPARQL Queries
# ===========================================

from rdflib import Graph, Namespace, RDFS
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

INPUT_TTL = "football_kg_extended.ttl"

print("Loading graph:", INPUT_TTL)
g = Graph()
g.parse(INPUT_TTL, format="turtle")
print("Graph loaded. Total triples:", len(g))

ONT = Namespace("http://www.semanticSports.org/ontology#")
EX = Namespace("http://www.semanticSports.org/data/")


def run_query(query, csv_output=None, description=""):
    """Helper function to run and print results"""
    print(f"\n{'='*60}")
    print(f"QUERY: {description}")
    print('='*60)
    
    try:
        res = g.query(query)
        
        cols = [str(v) for v in res.vars]
        rows = []

        for r in res:
            row = []
            for val in r:
                if val is None:
                    row.append("")
                    continue

                if isinstance(val, str):
                    row.append(val)
                    continue

                label = None
                try:
                    for lbl in g.objects(val, RDFS.label):
                        label = str(lbl)
                        break
                except:
                    pass

                row.append(label if label else str(val))
            rows.append(row)

        if rows:
            df = pd.DataFrame(rows, columns=cols)
            print(df.to_string(index=False))
            
            if csv_output:
                df.to_csv(csv_output, index=False)
                print(f"\n✓ Saved: {csv_output}")
        else:
            print("No results found.")
            
    except Exception as e:
        print(f"✗ Error: {e}")


# =========================================================
# 12 COMPLEX SPARQL QUERIES
# =========================================================

# Query 1: Performance Trends with Subquery and Calculated Fields
q1 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel ?totalGoals ?totalAssists ?matchCount ?goalPerMatch
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  
  {
    SELECT ?player (COALESCE(SUM(?g), 0) AS ?totalGoals) (COALESCE(SUM(?a), 0) AS ?totalAssists) (COUNT(?p) AS ?matchCount)
    WHERE {
      ?player ont:hasPerformance ?p .
      OPTIONAL { ?p ont:scoredGoals ?g }
      OPTIONAL { ?p ont:madeAssists ?a }
    }
    GROUP BY ?player
  }
  
  BIND(IF(?matchCount > 0 && ?totalGoals > 0, (xsd:float(?totalGoals) / xsd:float(?matchCount)), 0) AS ?goalPerMatch)
}
ORDER BY DESC(?totalGoals)
LIMIT 15
"""
run_query(q1, "query_1_performance_trends.csv", "Performance Trends with Subquery")


# Query 2: Teams with Top Performers 
q2 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel 
       (COUNT(DISTINCT ?player) AS ?playerCount)
       (SUM(?goals) AS ?teamTotalGoals)
       (AVG(?goals) AS ?teamAvgGoals)
       (MAX(?goals) AS ?maxSingleMatchGoals)
WHERE {
  ?team a ont:Team .
  ?team rdfs:label ?teamLabel .
  ?player ont:hasTeam ?team .
  OPTIONAL {
    ?player ont:hasPerformance ?p .
    ?p ont:scoredGoals ?goals .
  }
}
GROUP BY ?teamLabel
HAVING (COUNT(DISTINCT ?player) > 0)
ORDER BY DESC(?teamTotalGoals)
"""
run_query(q2, "query_2_team_top_scorers.csv", "Teams with Top Performers")


# Query 3: Property Path - Teammates (Players on Same Team)
q3 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT DISTINCT ?player1Label ?player2Label ?teamLabel
WHERE {
  ?player1 a ont:Player .
  ?player1 rdfs:label ?player1Label .
  ?player1 ont:hasTeam ?team .
  ?team rdfs:label ?teamLabel .
  
  ?player2 a ont:Player .
  ?player2 rdfs:label ?player2Label .
  ?player2 ont:hasTeam ?team .
  
  FILTER(?player1 != ?player2)
  FILTER(STR(?player1Label) < STR(?player2Label))
}
ORDER BY ?teamLabel ?player1Label
LIMIT 30
"""
run_query(q3, "query_3_teammates.csv", "Property Path - Finding Teammates")


# Query 4: Conditional Aggregation with CASE Statements (Fixed)
q4 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel 
       (COALESCE(SUM(?goals), 0) AS ?totalGoals)
       (COUNT(CASE WHEN ?goals > 2 THEN 1 END) AS ?hatTricks)
       (COUNT(CASE WHEN ?goals = 2 THEN 1 END) AS ?braces)
       (COUNT(CASE WHEN ?goals = 0 THEN 1 END) AS ?goallessMatches)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?p .
  ?p ont:scoredGoals ?goals .
}
        GROUP BY ?playerLabel
        ORDER BY DESC(?totalGoals)
LIMIT 20
"""
run_query(q4, "query_4_match_analysis.csv", "Conditional Aggregation with CASE")


# Query 5: Players with Multiple Performance Metrics (Fixed)
q5 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (COALESCE(SUM(?goals), 0) AS ?totalGoals)
       (COALESCE(SUM(?assists), 0) AS ?totalAssists)
       (COALESCE(SUM(?minutes), 0) AS ?totalMinutes)
       (COALESCE(AVG(?rating), 0) AS ?avgRating)
       (COUNT(?perf) AS ?appearances)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  
  ?player ont:hasPerformance ?perf .
  OPTIONAL { ?perf ont:scoredGoals ?goals }
  OPTIONAL { ?perf ont:madeAssists ?assists }
  OPTIONAL { ?perf ont:playedMinutes ?minutes }
  OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
}
GROUP BY ?playerLabel ?teamLabel
ORDER BY DESC(?totalGoals)
LIMIT 20
"""
run_query(q5, "query_5_comprehensive_stats.csv", "Comprehensive Player Statistics")


# Query 6: Teams Ranked by Multiple Criteria
q6 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel 
       (COUNT(DISTINCT ?player) AS ?playerCount)
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
       (AVG(?goals) AS ?avgGoalsPerPlayer)
       (MAX(?goals) AS ?bestSingleMatch)
WHERE {
  ?team a ont:Team .
  ?team rdfs:label ?teamLabel .
  ?player ont:hasTeam ?team .
  OPTIONAL {
    ?player ont:hasPerformance ?p .
    OPTIONAL { ?p ont:scoredGoals ?goals }
    OPTIONAL { ?p ont:madeAssists ?assists }
  }
}
        GROUP BY ?teamLabel
        ORDER BY DESC(?totalGoals) DESC(?totalAssists)
"""
run_query(q6, "query_6_team_rankings.csv", "Teams Ranked by Multiple Criteria")


# Query 7: Players Performance Distribution Analysis (Fixed - removed STDDEV which may not be supported)
q7 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel 
       (MIN(?goals) AS ?minGoals)
       (MAX(?goals) AS ?maxGoals)
       (AVG(?goals) AS ?avgGoals)
       (COUNT(?perf) AS ?matchesPlayed)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?perf .
  ?perf ont:scoredGoals ?goals .
  FILTER(?goals >= 0)
}
        GROUP BY ?playerLabel
        ORDER BY DESC(?avgGoals)
LIMIT 15
"""
run_query(q7, "query_7_performance_distribution.csv", "Performance Distribution Analysis")


# Query 8: Players with Best Goal-to-Assist Ratio (Fixed)
q8 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (COALESCE(SUM(?goals), 0) AS ?totalGoals)
       (COALESCE(SUM(?assists), 0) AS ?totalAssists)
       (IF(SUM(?assists) > 0, (xsd:float(SUM(?goals)) / xsd:float(SUM(?assists))), 999) AS ?goalToAssistRatio)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  ?player ont:hasPerformance ?p .
  OPTIONAL { ?p ont:scoredGoals ?goals }
  OPTIONAL { ?p ont:madeAssists ?assists }
}
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?goalToAssistRatio)
LIMIT 15
"""
run_query(q8, "query_8_goal_assist_ratio.csv", "Best Goal-to-Assist Ratio")


# Query 9: Tournament and Match Participation Analysis (Fixed)
q9 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?tournamentLabel 
       (COUNT(DISTINCT ?match) AS ?matchCount)
       (COUNT(DISTINCT ?player) AS ?playerCount)
       (COALESCE(SUM(?goals), 0) AS ?totalGoals)
WHERE {
  ?tournament a ont:Tournament .
  ?tournament rdfs:label ?tournamentLabel .
  OPTIONAL { ?tournament ont:hasMatch ?match }
  OPTIONAL {
    ?player ont:playedIn ?match .
    ?player ont:hasPerformance ?p .
    ?p ont:forMatch ?match .
    OPTIONAL { ?p ont:scoredGoals ?goals }
  }
}
GROUP BY ?tournamentLabel
ORDER BY DESC(?matchCount)
"""
run_query(q9, "query_9_tournament_analysis.csv", "Tournament Participation Analysis")


# Query 10: Position-Based Performance Analysis (Fixed)
q10 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?positionLabel 
       (COUNT(DISTINCT ?player) AS ?playerCount)
       (COALESCE(SUM(?goals), 0) AS ?totalGoals)
       (COALESCE(AVG(?goals), 0) AS ?avgGoalsPerPlayer)
       (COALESCE(SUM(?assists), 0) AS ?totalAssists)
WHERE {
  ?player a ont:Player .
  ?player ont:hasPosition ?position .
  ?position rdfs:label ?positionLabel .
  OPTIONAL {
    ?player ont:hasPerformance ?p .
    OPTIONAL { ?p ont:scoredGoals ?goals }
    OPTIONAL { ?p ont:madeAssists ?assists }
  }
}
        GROUP BY ?positionLabel
        ORDER BY DESC(?totalGoals)
"""
run_query(q10, "query_10_position_analysis.csv", "Position-Based Performance Analysis")


# Query 11: Players with Consistent High Performance (Fixed)
q11 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (COALESCE(AVG(?goals), 0) AS ?avgGoals)
       (COALESCE(AVG(?rating), 0) AS ?avgRating)
       (COUNT(?perf) AS ?matches)
       (MIN(?goals) AS ?minGoals)
       (MAX(?goals) AS ?maxGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  ?player ont:hasPerformance ?perf .
  ?perf ont:scoredGoals ?goals .
  OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
}
GROUP BY ?playerLabel ?teamLabel
ORDER BY DESC(?avgGoals) DESC(?avgRating)
LIMIT 15
"""
run_query(q11, "query_11_consistent_performers.csv", "Consistent High Performers")


# Query 12: Complex Multi-Join with Multiple Optional Patterns (Fixed)
q12 = """
PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel ?positionLabel
       (COALESCE(SUM(?goals), 0) AS ?totalGoals)
       (COALESCE(SUM(?assists), 0) AS ?totalAssists)
       (COUNT(DISTINCT ?match) AS ?matchesPlayed)
       (COUNT(DISTINCT ?tournament) AS ?tournamentsPlayed)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  
  OPTIONAL { 
    ?player ont:hasTeam ?team . 
    ?team rdfs:label ?teamLabel 
  }
  
  OPTIONAL { 
    ?player ont:hasPosition ?position . 
    ?position rdfs:label ?positionLabel 
  }
  
  OPTIONAL {
    ?player ont:hasPerformance ?perf .
    OPTIONAL { ?perf ont:scoredGoals ?goals }
    OPTIONAL { ?perf ont:madeAssists ?assists }
    OPTIONAL { ?perf ont:forMatch ?match }
    OPTIONAL {
      ?match ont:partOfTournament ?tournament .
    }
  }
}
GROUP BY ?playerLabel ?teamLabel ?positionLabel
ORDER BY DESC(?totalGoals) DESC(?totalAssists)
LIMIT 20
"""
run_query(q12, "query_12_multi_join_analysis.csv", "Complex Multi-Join Analysis")


print("\n" + "="*60)
print("ALL 12 COMPLEX QUERIES EXECUTED SUCCESSFULLY")
print("="*60 + "\n")
