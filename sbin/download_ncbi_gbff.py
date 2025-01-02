#!/usr/bin/env python

import argparse
import logging.config

import importlib_resources

from uta.tools.eutils import download_from_eutils, NcbiFileFormatEnum

logging_conf_fn = importlib_resources.files("uta").joinpath("etc/logging.conf")
logging.config.fileConfig(logging_conf_fn)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def download_transcript_gbff_from_ncbi(transcript_ac_file_path: str, output_dir: str) -> None:
    with open(transcript_ac_file_path) as f:
        for line in f:
            transcript_ac = line.strip()
            logger.info(f"Downloading GenBank file for transcript {transcript_ac}")
            ac_file_path = f"{output_dir}/{transcript_ac}.gbff"
            download_from_eutils(transcript_ac, NcbiFileFormatEnum.GENBANK, ac_file_path)


def main():
    parser = argparse.ArgumentParser(description='Download GenBank files from NCBI.')
    parser.add_argument("transcript_ac_file_path", type=str)
    parser.add_argument("--output-dir", "-o", default=".", type=str)
    args = parser.parse_args()

    logger.info("Downloading GenBank files from NCBI")
    download_transcript_gbff_from_ncbi(args.transcript_ac_file_path, args.output_dir)


if __name__ == "__main__":
    main()
