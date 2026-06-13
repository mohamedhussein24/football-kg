from rdflib import Graph

# Load the ontology
g = Graph()
g.parse(r"C:\Users\SE7S\Downloads\Web Science\football-kg\Football Web Semantics New.owl.rdf", format="xml")

print(f"Ontology loaded successfully with {len(g)} triples.")
