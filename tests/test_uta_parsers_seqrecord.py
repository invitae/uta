import os
import unittest

from Bio import SeqIO

from uta.parsers.seqrecord import SeqRecordFacade


class TestSeqRecordFacade_NM_001396027(unittest.TestCase):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    @classmethod
    def setUpClass(cls):
        gbff_file = os.path.join(cls.test_data_dir, 'rna.NM_001396027.gbff')
        seq_record = [sr for sr in SeqIO.parse(gbff_file, 'gb')][0]
        cls.seq_record_facade = SeqRecordFacade(seq_record)

    def test_id(self):
        assert self.seq_record_facade.id == 'NM_001396027.1'

    def test_gene_symbol(self):
        assert self.seq_record_facade.gene_symbol == 'FAM246C'

    def test_gene_id(self):
        assert self.seq_record_facade.gene_id == '117134596'

    def test_cds_se_i(self):
        assert self.seq_record_facade.cds_se_i == (0, 696)

    def test_exons_se_i(self):
        assert self.seq_record_facade.exons_se_i == [(0, 696)]


class TestSeqRecordFacade_NM_001996(unittest.TestCase):
    test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

    @classmethod
    def setUpClass(cls):
        gbff_file = os.path.join(cls.test_data_dir, 'rna.NM_001996.gbff')
        seq_record = [sr for sr in SeqIO.parse(gbff_file, 'gb')][0]
        cls.seq_record_facade = SeqRecordFacade(seq_record)

    def test_id(self):
        assert self.seq_record_facade.id == 'NM_001996.4'

    def test_gene_symbol(self):
        assert self.seq_record_facade.gene_symbol == 'FBLN1'

    def test_gene_id(self):
        assert self.seq_record_facade.gene_id == '2192'

    def test_cds_se_i(self):
        assert self.seq_record_facade.cds_se_i == (103, 2155)

    def test_exons_se_i(self):
        assert self.seq_record_facade.exons_se_i == [
            (0, 182),
            (182, 288),
            (288, 424),
            (424, 587),
            (587, 647),
            (647, 749),
            (749, 887),
            (887, 1025),
            (1025, 1169),
            (1169, 1298),
            (1298, 1424),
            (1424, 1544),
            (1544, 1676),
            (1676, 1800),
            (1800, 2251),
        ]


if __name__ == '__main__':
    unittest.main()
