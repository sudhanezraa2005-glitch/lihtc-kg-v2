from src.graph.config.neo4j_config import Neo4jConfig
from src.graph.relationships.load_county_metro_area import (
    CountyMetroAreaRelationshipLoader,
)

config = Neo4jConfig()
driver = config.get_driver()

try:
    loader = CountyMetroAreaRelationshipLoader(driver)
    stats = loader.load()
    print(stats)
finally:
    driver.close()