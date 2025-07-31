from neo4j import GraphDatabase

uri      = "bolt://localhost:7687"
user     = "neo4j"
password = "#Timothy1"

with open("create_tahr_graph.cypher") as f:
    cypher_script = f.read()

driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    session.run(cypher_script)      # ← no splitting!
print("✅ graph loaded")
driver.close()
