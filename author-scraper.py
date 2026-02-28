"""
Download PDFs of an author's papers from arXiv (no Google Cloud required).
Uses the public arXiv API; install with: pip install arxiv
"""
import os
import arxiv

def audit_author_papers(author_name, output_dir="./author_papers", max_results=5):
    """
    Search arXiv for papers by author_name and download their PDFs.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # arXiv API uses "au:Name" for author search
    query_author = author_name.replace(",", " ").strip()
    search_query = f"au:{query_author}"

    print(f"Searching arXiv for papers by: {author_name}...")
    search = arxiv.Search(query=search_query, max_results=max_results)
    client = arxiv.Client()

    count = 0
    for result in client.results(search):
        try:
            short_id = result.get_short_id().replace("/", "_")
            filename = f"{short_id}.pdf"
            result.download_pdf(dirpath=output_dir, filename=filename)
            count += 1
            title_short = (result.title[:50] + "...") if len(result.title) > 50 else result.title
            print(f"Downloaded: {short_id} | {title_short}")
        except Exception as e:
            print(f"Could not download {result.get_short_id()}: {e}")

    print(f"\nDone. Downloaded {count} PDF(s) to {output_dir}/")

# --- THIS WAS THE MISSING PART ---
if __name__ == "__main__":
    # Call the function here to make the script actually DO something
    # Example: "Geoffrey Hinton"
    audit_author_papers("Geoffrey Hinton", max_results=5)