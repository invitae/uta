import os
import unittest

from Bio import SeqIO

from uta.parsers.seqrecord import SeqRecordFacade


class TestSeqRecordFacade(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
