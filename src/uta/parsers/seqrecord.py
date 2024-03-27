from collections import defaultdict

import Bio.SeqRecord


class SeqRecordFacade:

    def __init__(self, seqrecord: Bio.SeqRecord.SeqRecord):
        self._sr = seqrecord

    @property
    def id(self):
        return self._sr.id

    @property
    def gene_symbol(self):
        genes = [f for f in self._sr.features if f.type == "gene"][0].qualifiers["gene"]
        assert len(genes) == 1
        return genes[0]

    @property
    def gene_id(self):
        # db_xref="GeneID:1234"
        db_xrefs = [f for f in self._sr.features if f.type == "gene"][0].qualifiers["db_xref"]
        gene_ids = [x.partition(":")[2] for x in db_xrefs if x.startswith("GeneID:")]
        assert len(gene_ids) == 1
        return gene_ids[0]

    @property
    def cds_se_i(self):
        try:
            cds = [f for f in self._sr.features if f.type == "CDS"][0]
        except IndexError:
            return None
        return (cds.location.start.real, cds.location.end.real)

    @property
    def exons_se_i(self):
        features_by_type = defaultdict(list)
        for feat in self._sr.features:
            features_by_type[feat.type].append(feat)

        if "exon" in features_by_type:
            exons = features_by_type["exon"]
        elif "ncRNA" in features_by_type:
            exons = features_by_type["ncRNA"]
            assert len(exons) == 1
        elif "misc_RNA" in features_by_type:
            exons = features_by_type["misc_RNA"]
            assert len(exons) == 1
        else:
            raise Exception("Unable to find or infer exons")
        se = [(f.location.start.real, f.location.end.real) for f in exons]

        return se
