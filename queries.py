from rdflib import Graph

g = Graph()
g.parse(r"C:\Users\SE7S\Downloads\Web Science\football-kg\Football Web Semantics New.owl.rdf", format="xml")

# Example SPARQL Query
q = """
PREFIX ont: <http://www.semanticSports.org/ontology#>

SELECT ?player ?team
WHERE {
    ?player a ont:Player .
    ?player ont:hasTeam ?team .
}
"""

results = g.query(q)

for row in results:
    player = row[0].split("#")[-1]
    team = row[1].split("#")[-1]
    print(f"Player: {player:20} Team: {team}")