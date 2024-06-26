import datetime
import unittest

import sqlalchemy
from sqlalchemy import text
import testing.postgresql

import uta
usam = uta.models


transcripts = {
    'NM_000680.2': {
        'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccgggtgagaagtaaaagctttttgcaggtctgctgctgtgtagggccctcaacccccagccttgacaagaaccatcaagttccaaccattaaggtccacaccatctccctcagtgagaacggggaggaagtctaggacaggaaagatgcagaggaaaggggaataatcttaggtacccaccccacttccttctcggaaggccagctcttcttggaggacaagacaggaccaatcaaagaggggacctgctgggaatggggtgggtggtagacccaactcatcaggcagcgggtagggcacagggaagagggagggtgtctcacaaccaaccagttcagaatgatacggaacagcatttccctgcagctaatgctttcttggtcactctgtgcccacttcaacgaaaaccaccatgggaaacagaatttcatgcacaatccaaaagactataaatataggattatgatttcatcatgaatattttgagcacacactctaagtttggagctatttcttgatggaagtgaggggattttattttcaggctcaacctactgacagccacatttgacatttatg',
        't_starts_i': [0, 1319], 			't_ends_i': [1319, 2281],			'names': ['1', '2b'],
        't_cds_start_i': 436, 				't_cds_end_i': 1837,
        'g_strand': -1,
        'g_starts_i': [26721603, 26627221], 		'g_ends_i': [26722922, 26628183],
        'g_cds_start_i': 26627665, 			'g_cds_end_i': 26722486,
        'pro_ac': 'NP_000671.2',
        'translation_exceptions': [
            {'start_position': 333, 'end_position': 335, 'amino_acid': 'Sec'},
            {'start_position': 589, 'end_position': 589, 'amino_acid': 'TERM'},
        ],
    },
    'NM_033302.2': {
        'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccggggacacacacccatgacatgaagccagcttcccgtccacgactgttgtccttactgcccaaggaaggggagcatgaaacccaccactggtcctgcgacccactgtctttggaatccaccccaggagcccaggagccttgcctgacacttggatttacttctttatcaagcatccatctgactaaggcacaaatccaacatgttactgttactgatacaggaaaaacagtaacttaaggaatgatcatgaatgcaaagggaaagaggaaaagagccttcagggacaaatagctcgattttttgtaaatcagtttcatacaacctccctcccccatttcattcttaaaagttaattgagaatcatcagccacgtgtagggtgtgag',
        't_starts_i': [0, 1319, 1705], 			't_ends_i': [1319, 1705, 2089], 			'names': ['1', '2a', '4'],
        't_cds_start_i': 436, 				't_cds_end_i': 1726,
        'g_strand': -1,
        'g_starts_i': [26721603, 26627797, 26613912], 	'g_ends_i': [26722922, 26628183, 26614296],
        'g_cds_start_i': 26614275, 			'g_cds_end_i': 26722486,
        'pro_ac': 'NP_150645.2',
    },
    'NM_033303.3': {
        'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccggacgaagtctcgctctgtcaccaggctggagtgcagtggcatgatcttggctcactgcaacctccgcctcccgggttcaagagattctcctgcctcagcctcccaagcagctgggactacagggatgtgccaccaggccgacgccaccaggcccagctaatttttgtatttttagtagagacggggtttcaccatgttggccaggatgatctcgatctcttgacctcatgatctgcctgcctcagcctcccaaagtgctgggattacaggcgtgagccaccgtgcccggcccaactattttttttttttatcttttttaacagtgcaatcctttctgtggatgaaatcttgctcagaagctcaatatgcaaaagaaagaaaaacagcagggctggacggatgttgggagtggggtaagaccccaaccactcagaaccacccccccaacacacacacacattctctccatggtgactggtgaggggcctctagagggtacatagtacaccatggagcacggtttaagcaccactggactacacattcttctgtggcagttatcttaccttcccatagacacccagcccatagccattggtt',
        't_starts_i': [0, 1319, 1705], 			't_ends_i': [1319, 1705, 2304], 			'names': ['1', '2a', '5'],
        't_cds_start_i': 436, 				't_cds_end_i': 1864,
        'g_strand': -1,
        'g_starts_i': [26721603, 26627797, 26605666], 	'g_ends_i': [26722922, 26628183, 26606265],
        'g_cds_start_i': 26606106, 			'g_cds_end_i': 26722486,
        'pro_ac': 'NP_150646.3',
    },
    'NM_033304.2': {
        'seq': 'gaattccgaatcatgtgcagaatgctgaatcttcccccagccaggacgaataagacagcgcggaaaagcagattctcgtaattctggaattgcatgttgcaaggagtctcctggatcttcgcacccagcttcgggtagggagggagtccgggtcccgggctaggccagcccggcaggtggagagggtccccggcagccccgcgcgcccctggccatgtctttaatgccctgccccttcatgtggccttctgagggttcccagggctggccagggttgtttcccacccgcgcgcgcgctctcacccccagccaaacccacctggcagggctccctccagccgagaccttttgattcccggctcccgcgctcccgcctccgcgccagcccgggaggtggccctggacagccggacctcgcccggccccggctgggaccatggtgtttctctcgggaaatgcttccgacagctccaactgcacccaaccgccggcaccggtgaacatttccaaggccattctgctcggggtgatcttggggggcctcattcttttcggggtgctgggtaacatcctagtgatcctctccgtagcctgtcaccgacacctgcactcagtcacgcactactacatcgtcaacctggcggtggccgacctcctgctcacctccacggtgctgcccttctccgccatcttcgaggtcctaggctactgggccttcggcagggtcttctgcaacatctgggcggcagtggatgtgctgtgctgcaccgcgtccatcatgggcctctgcatcatctccatcgaccgctacatcggcgtgagctacccgctgcgctacccaaccatcgtcacccagaggaggggtctcatggctctgctctgcgtctgggcactctccctggtcatatccattggacccctgttcggctggaggcagccggcccccgaggacgagaccatctgccagatcaacgaggagccgggctacgtgctcttctcagcgctgggctccttctacctgcctctggccatcatcctggtcatgtactgccgcgtctacgtggtggccaagagggagagccggggcctcaagtctggcctcaagaccgacaagtcggactcggagcaagtgacgctccgcatccatcggaaaaacgccccggcaggaggcagcgggatggccagcgccaagaccaagacgcacttctcagtgaggctcctcaagttctcccgggagaagaaagcggccaaaacgctgggcatcgtggtcggctgcttcgtcctctgctggctgccttttttcttagtcatgcccattgggtctttcttccctgatttcaagccctctgaaacagtttttaaaatagtattttggctcggatatctaaacagctgcatcaaccccatcatatacccatgctccagccaagagttcaaaaaggcctttcagaatgtcttgagaatccagtgtctctgcagaaagcagtcttccaaacatgccctgggctacaccctgcacccgcccagccaggccgtggaagggcaacacaaggacatggtgcgcatccccgtgggatcaagagagaccttctacaggatctccaagacggatggcgtttgtgaatggaaatttttctcttccatgccccgtggatctgccaggattacagtgtccaaagaccaatcctcctgtaccacagcccggaggggaatggattgtagatatttcaccaagaattgcagagagcatatcaagcatgtgaattttatgatgccaccgtggagaaagggttcagaatgctgatctccaggtagctggagacctaggcagtctgcaaatgaggagtcagctggaagctatggctatgtattatgtgacatcgcttgttcctaagtgaaaactggatatcccaaccttctggcccagtaggtttcatggttaagacctggtagtgagaacattttaggaactatttgcttgggcaggcaatttttcactct',
        't_starts_i': [0, 1319, 1705], 			't_ends_i': [1319, 1705, 2001], 			'names': ['1', '2a', '3'],
        't_cds_start_i': 436, 				't_cds_end_i': 1804,
        'g_strand': -1,
        'g_starts_i': [26721603, 26627797, 26623370], 	'g_ends_i': [26722922, 26628183, 26623666],
        'g_cds_start_i': 26623567, 			'g_cds_end_i': 26722486,
        'pro_ac': 'NP_150647.2',
    },
}


class TestUtaModels(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._postgresql = testing.postgresql.Postgresql()

        engine = sqlalchemy.create_engine(cls._postgresql.url())
        with engine.connect() as connection:
            connection.execute(text('drop schema if exists {schema} cascade'.format(schema=usam.schema_name)))
            connection.execute(text('create schema {schema}'.format(schema=usam.schema_name)))
            connection.commit()
        engine.dispose()

        cls.session = uta.connect(cls._postgresql.url())
        usam.Base.metadata.create_all(cls.session.bind.engine)

        # Test data are from:
        # http://www.ncbi.nlm.nih.gov/nuccore/NM_033304.2

        o = usam.Origin(
            name='NCBI',
            descr='Testing (originally NCBI, via Eutils)',
            url='http://bogus.com/',
            url_ac_fmt='http://bogus.com/{ac}',
        )
        cls.session.add(o)

        g = usam.Gene(
            gene_id='148',
            hgnc='ADRA1A',
            symbol='ADRA1A',
            maploc='8p21.2',
            descr='adrenoceptor alpha 1A',
            summary='''Alpha-1-adrenergic receptors (alpha-1-ARs) are
            members of the G protein-coupled receptor superfamily. They
            activate mitogenic responses and regulate growth and proliferation
            of many cells. There are 3 alpha-1-AR subtypes: alpha-1A, -1B and
            -1D, all of which signal through the Gq/11 family of G-proteins
            and different subtypes show different patterns of activation. This
            gene encodes alpha-1A-adrenergic receptor. Alternative splicing of
            this gene generates four transcript variants, which encode four
            different isoforms with distinct C-termini but having similar
            ligand binding properties. [provided by RefSeq, Jul 2008]'''.replace('\n', ' ')
        )
        cls.session.add(g)

        chr8_n = usam.Seq(
            seq='',
        )
        cls.session.add(chr8_n)

        chr8_sa_n = usam.SeqAnno(
            seq=chr8_n,
            origin=o,
            ac='NC_000008.10',
        )
        cls.session.add(chr8_sa_n)

        for ac, tx_info in transcripts.items():
            t_seq_n = usam.Seq(
                seq=tx_info['seq']
            )
            cls.session.add(t_seq_n)

            t_sa_n = usam.SeqAnno(
                seq=t_seq_n,
                origin=o,
                ac=ac,
            )
            cls.session.add(t_sa_n)

            t = usam.Transcript(
                ac=ac,
                origin=o,
                gene_id=g.gene_id,
                cds_start_i=tx_info['t_cds_start_i'],
                cds_end_i=tx_info['t_cds_end_i'],
                cds_md5='d41d8cd98f00b204e9800998ecf8427e',
            )
            cls.session.add(t)

            if 'translation_exceptions' in tx_info:
                for te in tx_info['translation_exceptions']:
                    te = usam.TranslationException(tx_ac=ac, **te)
                    cls.session.add(te)

            p = usam.AssociatedAccessions(
                tx_ac=ac,
                pro_ac=tx_info['pro_ac'],
                origin=o.name,
            )
            cls.session.add(p)

            # ExonSet and Exons on Transcript seq
            t_es = usam.ExonSet(
                tx_ac=ac,
                alt_ac=ac,
                alt_strand=1,
                alt_aln_method='transcript',
            )
            cls.session.add(t_es)

            for i, se in enumerate(zip(tx_info['t_starts_i'], tx_info['t_ends_i'], tx_info['names'])):
                e = usam.Exon(
                    exon_set=t_es,
                    start_i=se[0],
                    end_i=se[1],
                    name=se[2],
                    ord=i
                )
                cls.session.add(e)

            # ExonSet and Exons on chromosome seq
            g_es = usam.ExonSet(
                tx_ac=ac,
                alt_ac=chr8_sa_n.ac,
                alt_strand=tx_info['g_strand'],
                alt_aln_method='splign',
            )
            cls.session.add(g_es)

            for i, se in enumerate(zip(tx_info['g_starts_i'], tx_info['g_ends_i'])):
                e = usam.Exon(
                    exon_set=g_es,
                    start_i=se[0],
                    end_i=se[1],
                    ord=i,
                )
                cls.session.add(e)

        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        # kill the database (we started it)
        import signal
        cls._postgresql.stop(_signal=signal.SIGKILL)
        cls._postgresql.cleanup()

    def test_origin(self):
        all_origins = self.session.query(usam.Origin).all()
        self.assertEqual(len(all_origins), 1)

        o = all_origins[0]
        self.assertEqual(o.name, 'NCBI')
        self.assertEqual(o.url, 'http://bogus.com/')
        self.assertEqual(o.url_ac_fmt, 'http://bogus.com/{ac}')

        # NM_000680.2, NM_033302.2, NM_033303.3, NM_033304.2
        self.assertEqual(len(o.transcripts), 4)
        # self.assertEqual( len(o.dnaseqs)      , 5 ) ## NC_000008.10, + transcripts
        # self.assertEqual( len(o.exon_sets)  , 8 ) ## 4 transcripts *
        # {genomic,transcript}

    def test_gene(self):
        all_genes = self.session.query(usam.Gene).all()
        self.assertEqual(len(all_genes), 1)

        g = all_genes[0]
        self.assertEqual(g.descr, u'adrenoceptor alpha 1A')
        #self.assertEqual( g.maploc, u'8p21.2' )
        #self.assertEqual( g.strand, -1 )
        #self.assertEqual( g.strand_pm, u'-' )
        #self.assertEqual( len(g.transcripts), 4 )
        self.assertTrue(
            g.summary.startswith('Alpha-1-adrenergic receptors (alpha-1-ARs) are'))

    def test_dnaseq(self):
        all_dnaseqs = self.session.query(usam.Seq).all()
        self.assertEqual(len(all_dnaseqs), 5)

        n = self.session.query(usam.SeqAnno).filter(
            usam.SeqAnno.ac == 'NC_000008.10').one()
        self.assertEqual(n.ac, u'NC_000008.10')
        # self.assertTrue(len(n.exon_sets),2)
        self.assertEqual(n.origin.name, 'NCBI')
        #self.assertEqual(len(n.transcripts), 0)

        n = self.session.query(usam.SeqAnno).filter(
            usam.SeqAnno.ac == 'NM_000680.2').one()
        self.assertEqual(n.ac, u'NM_000680.2')
        # self.assertTrue(len(n.exon_sets),1)
        self.assertEqual(n.origin.name, 'NCBI')

        n = self.session.query(usam.Seq).join(usam.Seq.aliases).filter(
            usam.SeqAnno.ac == 'NM_000680.2').one()
        self.assertEqual(len(n.seq), 2281)
        self.assertTrue(n.seq.startswith('gaattccgaa'))
        self.assertTrue(n.seq.endswith('gacatttatg'))
        #self.assertEqual(len(n.transcripts), 1)

    def test_exon_set(self):
        all_exon_sets = self.session.query(usam.Seq).all()
        self.assertTrue(len(all_exon_sets), 8)

        exon_sets = self.session.query(usam.ExonSet).filter(
            usam.ExonSet.tx_ac == 'NM_000680.2')

        # http://www.ncbi.nlm.nih.gov/nuccore/NM_000680.2
        ## es = [ es for es in exon_sets if es.is_primary ][0]
        ## self.assertEqual( (es.cds_start_i,es.cds_end_i), (436, 1837) )
        ## self.assertEqual( len(es.exons), 2 )
        ## self.assertEqual( es.is_primary, True )
        ## self.assertEqual( es.ref_dnaseq.ac, 'NM_000680.2' )
        ## self.assertEqual( es.strand, 1 )
        ## self.assertEqual( es.transcript.ac, 'NM_000680.2' )

        # seq_gene.md.gz:
        # 9606	8	26627222	26627665	-	NT_167187.1	14485368	14485811	-	NM_000680.2	GeneID:148	UTR	GRCh37.p10-Primary Assembly	NM_000680.2	-
        # 9606	8	26627666	26628183	-	NT_167187.1	14485812	14486329	-	NP_000671.2	GeneID:148	CDS	GRCh37.p10-Primary Assembly	NM_000680.2	-
        # 9606	8	26721604	26722486	-	NT_167187.1	14579750	14580632	-	NP_000671.2	GeneID:148	CDS	GRCh37.p10-Primary Assembly	NM_000680.2	-
        # 9606	8	26722487	26722922	-	NT_167187.1	14580633	14581068	-	NM_000680.2	GeneID:148	UTR	GRCh37.p10-Primary Assembly	NM_000680.2	-
        ## es = [ es for es in exon_sets if not es.is_primary ][0]
        ## self.assertEqual( (es.cds_start_i,es.cds_end_i), (26627665, 26722486) )
        ## self.assertEqual( len(es.exons), 2 )
        ## self.assertEqual( es.is_primary, False )
        ## self.assertEqual( es.ref_dnaseq.ac, 'NC_000008.10' )
        ## self.assertEqual( es.strand, -1 )
        ## self.assertEqual( es.transcript.ac, 'NM_000680.2' )

    def test_exon(self):
        t = self.session.query(usam.Transcript).filter(
            usam.Transcript.ac == 'NM_000680.2').one()
        #es = [ es for es in t.exon_sets if es.is_primary ][0]
        #self.assertEqual( (es.exons[0].start_i,es.exons[0].end_i) , (0,1319) )
        #self.assertEqual( (es.exons[1].start_i,es.exons[1].end_i) , (1319,2281) )

    def test_associated_accessions(self):
        all_aa = self.session.query(usam.AssociatedAccessions).all()
        self.assertEqual(len(all_aa), 4)
        # check values in one row:
        aa = self.session.query(usam.AssociatedAccessions).filter_by(tx_ac='NM_000680.2').one()
        self.assertIsInstance(aa.associated_accession_id, int)
        self.assertIsInstance(aa.added, datetime.datetime)
        self.assertEqual(aa.tx_ac, 'NM_000680.2')
        self.assertEqual(aa.pro_ac, 'NP_000671.2')
        self.assertEqual(aa.origin, 'NCBI')

    def test_associated_accessions_transcript_not_in_database(self):
        """
        Should create row in associated_accessions even for transcripts not in database.
        This is only the case until associated_accessions.tx_ac is converted to a transcript foreign key.
        """
        p = usam.AssociatedAccessions(
            tx_ac='dummy_transcript',
            pro_ac='dummy_protein',
            origin='dummy_origin',
        )
        self.session.add(p)
        self.session.commit()
        aa = self.session.query(usam.AssociatedAccessions).filter_by(tx_ac='dummy_transcript').one()
        self.assertEqual(aa.tx_ac, 'dummy_transcript')
        self.assertEqual(aa.pro_ac, 'dummy_protein')
        self.assertEqual(aa.origin, 'dummy_origin')

    def test_translation_exception(self):
        """
        Should create rows in translation_exception table.
        """
        translation_exceptions = self.session.query(usam.TranslationException).filter_by(tx_ac='NM_000680.2').all()
        self.assertEqual(len(translation_exceptions), 2)

    def test_translation_exception_start_not_greater_than_end(self):
        """
        Should not create row in translation_exception table if start is greater than end.
        """
        te = usam.TranslationException(
            tx_ac='NM_033302.2',
            start_position=100,
            end_position=99,
            amino_acid='dummy_aa',
        )
        self.session.add(te)

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            self.session.commit()

        # allow session to be used after failure
        self.session.rollback()

        # translation exception should not exist because transaction failed
        translation_exceptions = self.session.query(usam.TranslationException).filter_by(tx_ac='NM_033302.2').all()
        self.assertEqual(translation_exceptions, [])


if __name__ == '__main__':
    unittest.main()

# <LICENSE>
# Copyright 2014 UTA Contributors (https://bitbucket.org/biocommons/uta)
##
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
##
# http://www.apache.org/licenses/LICENSE-2.0
##
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
