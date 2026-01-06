from pymongo.operations import SearchIndexModel

def ensure_vector_index(db, collection_name: str, num_dimensions: int = 768):
    collection = db[collection_name]
    try:
        # Revisar si ya existe
        existing = list(collection.list_search_indexes())
        if existing:
            return

        search_index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": num_dimensions,
                        "similarity": "cosine",
                    }
                ]
            },
            name="default_vector_index",
            type="vectorSearch",
        )
        collection.create_search_index(model=search_index_model)
    except Exception as e:
        import logging
        logging.warning(f"Vector index could not be created: {e}")
