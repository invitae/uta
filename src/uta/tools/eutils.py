import logging

import requests

from uta import EutilsDownloadError

logger = logging.getLogger(__name__)


def download_from_eutils(accession: str, file_format: str, output_file: str) -> None:
    """
    Download a file from NCBI using the eutils endpoint.
    Args:
    - accession: NCBI accession ID
    - file_format: File format to download ("fasta" or "gb")
    - output_file: Path to the file where the downloaded content will be saved
    """
    if file_format not in ["fasta", "gb"]:
        raise ValueError("file_format must be either 'fasta' or 'gb'")

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "nuccore",
        "id": accession,
        "retmode": "text",
        "rettype": file_format
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        with open(output_file, 'w') as file:
            file.write(response.text)
    else:
        raise EutilsDownloadError(f"Failed to download {file_format} file for {accession}. HTTP status code: {response.status_code}")