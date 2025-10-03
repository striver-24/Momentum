import os
import chromadb
from sentence_transformers import SentenceTransformer
import logging
from ..config.config_loader import get_config, get_model_config, get_vector_db_config, get_file_paths

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VectorDBConnector:
    def __init__(self, db_path=None):
        try:
            config = get_config()
            embedding_config = get_model_config('embedding')
            vector_db_config = get_vector_db_config()
            
            model_name = embedding_config['name']
            show_progress = embedding_config.get('show_progress', True)
            
            logging.info(f"Loading sentence transformer model: {model_name}...")
            self.model = SentenceTransformer(model_name)
            logging.info("Embedding model loaded successfully.")

            db_path = db_path or vector_db_config['path']
            self.client = chromadb.PersistentClient(path=db_path)

            self.collection_name = vector_db_config['collection_name']
            logging.info(f"Accessing ChromaDB collection: {self.collection_name}")
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logging.info("Vector DB Connector initialized successfully.")

        except Exception as e:
            logging.error(f"Failed to initialize VectorDBConnector: {e}", exc_info=True)
            raise

    def _get_code_files(self, root_dir: str) -> list[str]:
        code_files = []
        file_config = get_file_paths()
        ignore_dirs = set(file_config['ignore_dirs'])
        ignore_extensions = set(file_config['ignore_extensions'])

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

            for filename in filenames:
                if os.path.splitext(filename)[1] not in ignore_extensions:
                    code_files.append(os.path.join(dirpath, filename))
        return code_files

    def populate_from_directory(self, workspace_dir: str):
        logging.info(f"Scanning directory '{workspace_dir}' to populate vector database...")
        files_to_process = self._get_code_files(workspace_dir)

        if not files_to_process:
            logging.warning("No code files found to populate the database.")
            return

        documents, metadatas, ids = [], [], []

        for file_path in files_to_process:
            try:
                if self.collection.get(ids=[file_path])['ids']:
                    logging.info(f"Skipping already indexed file: {file_path}")
                    continue

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content.strip():
                        documents.append(content)
                        metadatas.append({"source": file_path})
                        ids.append(file_path)
            except Exception as e:
                logging.warning(f"Could not read or process file {file_path}: {e}")

        if not documents:
            logging.info("No new files to add to the vector database.")
            return

        embedding_config = get_model_config('embedding')
        show_progress = embedding_config.get('show_progress', True)
        
        logging.info(f"Generating embeddings for {len(documents)} new documents...")
        embeddings = self.model.encode(documents, show_progress_bar=show_progress).tolist()

        logging.info("Adding new documents to ChromaDB collection...")
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logging.info("Successfully populated vector database from directory.")

    def query_codebase(self, query_text: str, n_results: int = 5) -> list[str]:
        if not query_text:
            return []

        logging.info(f"Querying vector database with: '{query_text[:60]}...'")
        query_embedding = self.model.encode([query_text]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents"]
        )

        retrieved_docs = results.get('documents', [[]])[0]
        logging.info(f"Retrieved {len(retrieved_docs)} relevant code snippets.")
        return retrieved_docs

    def clear_collection(self):
        logging.warning(f"Clearing all documents from collection '{self.collection_name}'...")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        logging.info("Collection cleared successfully.")
