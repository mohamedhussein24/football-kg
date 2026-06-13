import requests
import json

BASE_URL = "http://127.0.0.1:5000"

queries = [
    {
      "name": '1. Top Goal Scorers',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel (SUM(?g) AS ?totalGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?p .
  ?p ont:scoredGoals ?g .
}
GROUP BY ?playerLabel
ORDER BY DESC(?totalGoals)
LIMIT 15"""
    },
    {
      "name": '2. Performance Trends',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel ?totalGoals ?totalAssists
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  
  {
    SELECT ?player (SUM(?g) AS ?totalGoals) (SUM(?a) AS ?totalAssists)
    WHERE {
      ?player ont:hasPerformance ?p .
      OPTIONAL { ?p ont:scoredGoals ?g }
      OPTIONAL { ?p ont:madeAssists ?a }
    }
    GROUP BY ?player
  }
}
ORDER BY DESC(?totalGoals)
LIMIT 15"""
    },
    {
      "name": '3. Teams with Top Performers',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel ?topScorer ?topScorerGoals ?teamTotalGoals
WHERE {
  ?team a ont:Team .
  ?team rdfs:label ?teamLabel .
  
  {
    SELECT ?team (MAX(?playerGoals) AS ?topScorerGoals) ?topScorer
    WHERE {
      ?player ont:hasTeam ?team .
      ?player rdfs:label ?topScorer .
      {
        SELECT ?player (SUM(?g) AS ?playerGoals)
        WHERE {
          ?player ont:hasPerformance ?p .
          ?p ont:scoredGoals ?g .
        }
        GROUP BY ?player
      }
    }
    GROUP BY ?team ?topScorer
  }
  
  {
    SELECT ?team (SUM(?g) AS ?teamTotalGoals)
    WHERE {
      ?player ont:hasTeam ?team .
      ?player ont:hasPerformance ?p .
      ?p ont:scoredGoals ?g .
    }
    GROUP BY ?team
  }
}
ORDER BY DESC(?teamTotalGoals)"""
    },
    {
      "name": '4. Comprehensive Player Stats',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
       (AVG(?rating) AS ?avgRating)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  
  ?player ont:hasPerformance ?perf .
  OPTIONAL { ?perf ont:scoredGoals ?goals }
  OPTIONAL { ?perf ont:madeAssists ?assists }
  OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
}
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?totalGoals)
LIMIT 20"""
    },
    {
      "name": '5. Teams Ranked by Multiple Criteria',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?teamLabel 
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
       (AVG(?goals) AS ?avgGoalsPerPlayer)
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
        ORDER BY DESC(?totalGoals) DESC(?totalAssists)"""
    },
    {
      "name": '6. Performance Distribution',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel 
       (AVG(?goals) AS ?avgGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  ?player ont:hasPerformance ?perf .
  ?perf ont:scoredGoals ?goals .
}
        GROUP BY ?playerLabel
        ORDER BY DESC(?avgGoals)
LIMIT 15"""
    },
    {
      "name": '7. Goal-to-Assist Ratio',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (SUM(?goals) AS ?totalGoals)
       (SUM(?assists) AS ?totalAssists)
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
        ORDER BY ASC(?goalToAssistRatio)
LIMIT 15"""
    },
    {
      "name": '8. Position-Based Analysis',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?positionLabel 
       (SUM(?goals) AS ?totalGoals)
       (AVG(?goals) AS ?avgGoalsPerPlayer)
       (SUM(?assists) AS ?totalAssists)
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
ORDER BY DESC(?totalGoals)"""
    },
    {
      "name": '9. Consistent Performers',
      "query": """PREFIX ont: <http://www.semanticSports.org/ontology#>
SELECT ?playerLabel ?teamLabel 
       (AVG(?rating) AS ?avgRating)
       (AVG(?goals) AS ?avgGoals)
WHERE {
  ?player a ont:Player .
  ?player rdfs:label ?playerLabel .
  OPTIONAL { ?player ont:hasTeam ?team . ?team rdfs:label ?teamLabel . }
  ?player ont:hasPerformance ?perf .
  ?perf ont:scoredGoals ?goals .
  OPTIONAL { ?perf ont:hasPerformanceRating ?rating }
}
        GROUP BY ?playerLabel ?teamLabel
        ORDER BY DESC(?avgRating) DESC(?avgGoals)
LIMIT 15"""
    }
]

integrated_types = [
    'top_scorers_enriched',
    'young_talents',
    'physicality_analysis',
    'club_country',
    'player_awards'
]

print("--- Checking Standard Queries ---")
for q in queries:
    print(f"Testing: {q['name']}")
    try:
        res = requests.post(f"{BASE_URL}/api/query", json={"query": q['query']})
        if res.status_code == 200:
            data = res.json()
            if "rows" in data:
                count = len(data["rows"])
                print(f"  -> Success: {count} rows")
                if count == 0:
                     print("  -> WARNING: 0 ROWS")
            else:
                 print("  -> Unexpected format")
        else:
            print(f"  -> Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"  -> Exception: {e}")

print("\n--- Checking Integrated Queries ---")
for t in integrated_types:
    print(f"Testing: {t}")
    try:
        res = requests.post(f"{BASE_URL}/api/query/integrated", json={"type": t})
        if res.status_code == 200:
            data = res.json()
            if "rows" in data:
                print(f"  -> Success: {len(data['rows'])} rows")
            else:
                 print("  -> Unexpected format")
        else:
            print(f"  -> Error {res.status_code}: {res.text}")
    except Exception as e:
         print(f"  -> Exception: {e}")
