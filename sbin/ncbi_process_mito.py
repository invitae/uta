"""
Download mito fasta and gbff file.
"""
import argparse
from collections import Counter
import dataclasses
import logging
import logging.config
import math
from pathlib import Path
import pkg_resources
import requests
from typing import Dict, Optional

import Bio.SeqIO
from bioutils.digests import seq_md5
from more_itertools import first, one

from uta.formats.geneaccessions import GeneAccessions, GeneAccessionsWriter
from uta.formats.seqinfo import SeqInfo, SeqInfoWriter
from uta.formats.txinfo import TxInfo, TxInfoWriter
from uta.formats.exonset import ExonSet, ExonSetWriter


@dataclasses.dataclass
class MitoGeneData:
    gene_id: int
    gene_symbol: str
    name: str
    tx_ac: str
    tx_seq: str
    tx_start: int
    tx_end: int
    alt_ac: str
    alt_start: int
    alt_end: int
    strand: str
    transl_table: str
    origin: str = "NCBI"
    transl_except: Optional[str] = None
    pro_ac: Optional[str] = None
    pro_seq: Optional[str] = None

    def exons_se_i(self) -> str:
        return f"{self.tx_start},{self.tx_end}"

    def cds_se_i(self) -> str:
        value = ''
        if self.pro_ac is not None:
            value = self.exons_se_i()
        return value


logging_conf_fn = pkg_resources.resource_filename(
    "uta", "etc/logging.conf")
logging.config.fileConfig(logging_conf_fn)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument("accession", type=str)
    parser.add_argument("--output-dir", "-o", default=".", type=str)
    arguments = parser.parse_args(argv)
    return arguments


def download(url_str, local_path):
    logger.info(f"downloading {url_str} to {local_path}")

    # get total:
    response = requests.get(url_str, stream=True)

    with open(local_path, "wb") as handle:
        for data in response.iter_content():
            handle.write(data)


def check_mito_files(output_dir: str, accession: str) -> Dict[str, Path]:
    # TODO: replace with built in utility
    ncbi_fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={}&retmode=text&rettype={}"
    mt_gb_filepath = Path(output_dir) / Path(f"{accession.split('.')[0]}.gbff")
    mt_fa_filepath = Path(output_dir) / Path(f"{accession.split('.')[0]}.fna")

    if any([not file.exists() for file in (mt_gb_filepath, mt_fa_filepath)]):
        # get gbff
        download(url_str=ncbi_fetch_url.format(accession, "gb"), local_path=mt_gb_filepath)
        # get fasta
        download(
            url_str=ncbi_fetch_url.format(accession, "fasta"), local_path=mt_fa_filepath
        )
    else:
        logger.info(f"Previously downloaded files for {accession} have been found")
        logger.info(f"  - GBFF: {mt_gb_filepath}")
        logger.info(f"  - FNA: {mt_fa_filepath}")

    return {"gbff": mt_gb_filepath, "fna": mt_fa_filepath}


def parse_db_xrefs(gb_feature):
    """
    Example:
        Key: db_xref
        Value: ['GeneID:4558', 'HGNC:HGNC:7481', 'MIM:590070']
    """
    if "db_xref" in gb_feature.qualifiers:
        return {
            x[0]: x[-1]
            for x in list(map(lambda x: x.split(":"), gb_feature.qualifiers["db_xref"]))
        }
    return {}


def parse_nomenclature_value(gb_feature):
    """
    Example:
        Key: nomenclature
        Value: ['Official Symbol: MT-TF | Name: mitochondrially encoded tRNA phenylalanine | Provided by: HGNC:HGNC:7481']
    """
    results = {}

    nomenclature_list = list(
        map(lambda x: x.strip(), one(gb_feature.qualifiers["nomenclature"]).split("|"))
    )
    for nomenclature in nomenclature_list:
        key, value = nomenclature.split(":")
        results[key.strip()] = value.strip()

    return results


def get_mito_features(gbff_filepath: str):
    logger.info(f"processing NCBI GBFF file from {gbff_filepath}")
    with open(gbff_filepath) as fh:
        for record in Bio.SeqIO.parse(fh, "gb"):
            for feature in record.features:
                xrefs = parse_db_xrefs(feature)

                # slice sequence using feature location
                feature_start, feature_end = (
                    feature.location.start,
                    feature.location.end,
                )
                feature_seq = record.seq[feature_start:feature_end]
                strand = "+"
                if feature.location.strand == -1:
                    strand = "-"
                    feature_seq = feature_seq.reverse_complement()
                    feature_start, feature_end = feature_end, feature_start

                # dependent on feature type, process data and output if appropriate
                if feature.type == "gene":
                    # for gene feature do not yield anything, just set gene level attributes
                    gene_id = int(xrefs["GeneID"])
                    nomenclature = parse_nomenclature_value(feature)
                    hgnc = nomenclature["Official Symbol"]
                    name = nomenclature["Name"]
                    ac = f"{record.id}_{feature.location.start}_{feature.location.end}"

                elif feature.type in ("tRNA", "rRNA", "CDS"):
                    assert int(xrefs["GeneID"]) == gene_id
                    # if feature type not CDS, set defaults
                    pro_ac = None
                    pro_seq = None
                    transl_table = None
                    transl_except = None

                    if feature.type == "CDS":
                        # override defaults for CDS features
                        pro_ac = one(feature.qualifiers["protein_id"])
                        pro_seq = one(feature.qualifiers["translation"])
                        transl_table = one(feature.qualifiers["transl_table"])
                        if "transl_except" in feature.qualifiers:
                            transl_except = one(feature.qualifiers["transl_except"])

                # yield gene data
                yield MitoGeneData(
                    gene_id=gene_id,
                    gene_symbol=hgnc,
                    name=name,
                    tx_ac=ac,
                    tx_seq=feature_seq,
                    tx_start=0,
                    tx_end=feature.location.end - feature.location.start,
                    alt_ac=record.id,
                    alt_start=feature_start,
                    alt_end=feature_end,
                    strand=strand,
                    transl_table=transl_table,
                    transl_except=transl_except,
                    pro_ac=pro_ac,
                    pro_seq=pro_seq,
                )


def main(ncbi_accession: str, output_dir: str):
    # get input files
    input_files = check_mito_files(output_dir=output_dir, accession=ncbi_accession)

    # extract Mitochondrial gene information
    mito_genes = [mg for mf in input_files.values() for mg in get_mito_features(mf)]
    logger.info(f"found {len(mito_genes)} genes from parsing {input_files['gbff']}")

    logger.info(f"found {Counter(gene_types)} from parsing {input_files['gbff']}")


if __name__ == "__main__":
    args = parse_args()

    main(args.output_dir, args.accession)
