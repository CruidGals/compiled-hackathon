import os
from google.cloud import bigquery
from google.cloud import storage

def audit_author_papers(author_name, output_dir="./author_papers"):
    # 1. Initialize Clients
    bq_client = bigquery.Client()
    storage_client = storage.Client()
    bucket = storage_client.bucket("arxiv-dataset")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. Search BigQuery for IDs
    # We use a wildcard search for the name format 'Surname, First'
    query = """
        SELECT id, title 
        FROM `kaggle-public-data.arxiv.metadata` 
        WHERE authors LIKE @author
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("author", "STRING", f"%{author_name}%")
        ]
    )
    
    print(f"🔎 Searching for papers by: {author_name}...")
    query_job = bq_client.query(query, job_config=job_config)
    results = list(query_job.result())
    
    print(f"✅ Found {len(results)} papers. Starting downloads...\n")

    # 3. Download the PDFs
    for row in results:
        paper_id = row.id
        # ArXiv bucket structure: arxiv/arxiv/pdf/YYMM/ID.pdf
        yymm = paper_id.split('.')[0]
        blob_path = f"arxiv/arxiv/pdf/{yymm}/{paper_id}.pdf"
        local_path = os.path.join(output_dir, f"{paper_id}.pdf")

        blob = bucket.blob(blob_path)
        
        try:
            blob.download_to_filename(local_path)
            print(f"📥 Downloaded: {paper_id} | {row.title[:50]}...")
        except Exception as e:
            # Some very old papers or newly updated ones might have different paths
            print(f"⚠️ Could not find PDF for {paper_id}: {e}")

# --- EXECUTION ---
# For ArXiv, use "Surname, First Name" or just "Surname"
audit_author_papers("Hinton, Geoffrey")