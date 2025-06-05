import chromadb

client = chromadb.HttpClient()

collection = client.create_collection("test")

collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about oranges"
    ],
    ids=["id1", "id2"]
)
