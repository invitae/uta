#!/usr/bin/env python

import argparse
import logging.config
import sys

import importlib_resources

from uta.formats.exonset import ExonSetReader, ExonSetWriter
from uta.tools.file_utils import open_file

logging_conf_fn = importlib_resources.files("uta").joinpath("etc/logging.conf")
logging.config.fileConfig(logging_conf_fn)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Coalesce exonsets.')
    parser.add_argument('exonsets', nargs="+", help='Path to the exonset file')
    args = parser.parse_args()

    logger.info(f"Coalescing exonsets from {len(args.exonsets)} files")
    esw = ExonSetWriter(sys.stdout)
    seen_ess: Dict[Tuple[str, str], str] = {}
    skipped = 0

    for exonset_fn in args.exonsets:
        logger.info(f"  - processing exonset file {exonset_fn}")
        with open_file(exonset_fn) as f:
            exonsets = ExonSetReader(f)
            for exonset in exonsets:
                key = (exonset.tx_ac, exonset.alt_ac)
                if key in seen_ess:
                    logger.warning(f"  - exon set for transcript {exonset.tx_ac}/{exonset.alt_ac} already "
                                   f"seen in {seen_ess[(exonset.tx_ac, exonset.alt_ac)]}. Skipping.")
                    skipped += 1
                else:
                    seen_ess[key] = exonset_fn
                    esw.write(exonset)

    logger.info(f"Coalesced {len(seen_ess)} exonsets from {len(args.exonsets)} files, skipped {skipped} duplicates.")


if __name__ == '__main__':
    main()
