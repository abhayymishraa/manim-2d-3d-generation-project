import time
from dotenv import load_dotenv
from app.config import settings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter, HTMLSemanticPreservingSplitter
from langchain_community.document_loaders import BSHTMLLoader, DirectoryLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

load_dotenv()

# Gemini embeddings
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def ingest_docs():
    # Load HTML docs
    loader = DirectoryLoader(
        "manim-docs/docs.manim.community/en/stable/",
        glob="**/*.html",
        loader_cls=BSHTMLLoader,
    )
    raw_documents = loader.load()
    print(f"Loaded {len(raw_documents)} raw documents")

    # Semantic HTML splitting
    html_splitter = HTMLSemanticPreservingSplitter(
        headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2"), ("h3", "Header 3")],
        max_chunk_size=1000,
        separators=["\n\n", "\n", ".", " "],
        elements_to_preserve=["code", "pre", "table", "ul", "ol"],
        preserve_images=False,
        preserve_videos=False,
    )
    html_chunks = []
    for doc in raw_documents:
        chunks = html_splitter.split_text(doc.page_content)
        # split if no chunk exist(error when no chunks)
        if not chunks:
            continue  
        for chunk in chunks:
            html_chunks.append(chunk if isinstance(chunk, Document) else Document(page_content=chunk))

    # Character splitting
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " "],
    )
    split_docs = char_splitter.split_documents(html_chunks)
    print(f"Split into {len(split_docs)} final chunks")

    # Batch processing
    batch_size = 100
    max_retries = 5

    for i in range(0, len(split_docs), batch_size):
        batch = split_docs[i:i + batch_size]
        attempt = 0
        while attempt < max_retries:
            try:
                print(
                    f"Processing batch {i // batch_size + 1} with {len(batch)} documents, attempt {attempt + 1}"
                )
                PineconeVectorStore.from_documents(
                    batch,
                    embedding,
                    index_name="newformanim",
                )
                print(f"Batch {i // batch_size + 1} added to Pinecone")
                break
            except Exception as e:
                if "ResourceExhausted" in str(e):
                    wait_time = 2 ** attempt * 5
                    print(f"Quota exceeded, retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
                    attempt += 1
                else:
                    raise
        else:
            print(f"Failed to process batch {i // batch_size + 1} after {max_retries} retries. Skipping.")
        time.sleep(0.25)

    print("**** Loading to vectorstore complete ****")

if __name__ == "__main__":
    ingest_docs()
