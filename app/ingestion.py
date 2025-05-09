import time
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from langchain_community.document_loaders import BSHTMLLoader
from langchain.document_loaders import DirectoryLoader
from langchain_text_splitters import HTMLSemanticPreservingSplitter
from langchain_cohere import CohereEmbeddings
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


load_dotenv()

embedding = CohereEmbeddings(
    model="embed-v4.0",
    cohere_api_key=settings.COHERE_API_KEY,
    user_agent="LangChain",
)


def ingest_docs():

    loader = DirectoryLoader(
        "manim-docs/docs.manim.community/en/stable/",
        glob="**/*.html",
        loader_cls=BSHTMLLoader,
    )
    raw_documents = loader.load()
    print(f"loaded {len(raw_documents)} documents")

    html_splitter = HTMLSemanticPreservingSplitter(
        headers_to_split_on=[
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ],
        max_chunk_size=1000,
        separators=["\n\n", "\n", ".", " "],
        elements_to_preserve=["code", "pre", "table", "ul", "ol"],
        preserve_images=False,
        preserve_videos=False,
    )


    html_chunks = []
    for doc in raw_documents:
        html_chunks.append(doc)

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "],
    )

    header_splits = char_splitter.split_documents(html_chunks)

    print(f"Split into {len(header_splits)} chunks")

    batch_size = 100
    max_retries = 5

    for i in range(0, len(header_splits), batch_size):
        batch = header_splits[i : i + batch_size]
        attempt = 0
        while attempt < max_retries:
            try:
                print(
                    f"Processing batch {i // batch_size + 1} with {len(batch)} documents, attempt {attempt + 1}"
                )
                PineconeVectorStore.from_documents(
                    batch,
                    embedding,
                    index_name=settings.PINECONE_INDEX_NAME,
                )
                print(f"Batch {i // batch_size + 1} added to Pinecone")
                break
            except Exception as e:
                if "ResourceExhausted" in str(e):
                    wait_time = (
                        2**attempt * 5
                    )  # exponential backoff with base 5 seconds
                    print(f"Quota exceeded, retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
                    attempt += 1
                else:
                    raise
        else:
            print(
                f"Failed to process batch {i // batch_size + 1} after {max_retries} retries. Skipping."
            )

        time.sleep(0.25)

    print("****Loading to vectorstore done ***")


if __name__ == "__main__":
    ingest_docs()
