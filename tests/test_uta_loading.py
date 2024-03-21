import configparser
import signal
import unittest

import sqlalchemy as sa
import testing.postgresql

import uta
import uta.loading as ul
import uta.models as usam


class TestUtaLoading(unittest.TestCase):

    def setUp(self):
        self.db = testing.postgresql.Postgresql()
        self.session = uta.connect(self.db.url())
        self.session.execute(sa.text('drop schema if exists {schema} cascade'.format(schema=usam.schema_name)))
        self.session.execute(sa.text('create schema {schema}'.format(schema=usam.schema_name)))
        self.session.commit()

        # create all uta tables
        usam.Base.metadata.create_all(self.session.bind.engine)

    def tearDown(self):
        self.session.close()
        self.db.stop(_signal=signal.SIGKILL)
        self.db.cleanup()

    def test_load_assoc_ac(self):
        """
        Test loading file tests/data/assocacs.gz
        """

        # insert origins referenced in data file
        o1 = usam.Origin(
            name='NCBI',
            url='http://bogus.com/ncbi',
            url_ac_fmt='http://bogus.com/ncbi/{ac}',
        )
        o2 = usam.Origin(
            name='DummyOrigin',
            url='http://bogus.com/dummy',
            url_ac_fmt='http://bogus.com/dummy/{ac}',
        )
        self.session.add(o1)
        self.session.add(o2)

        # insert transcripts referenced in data file
        t1 = usam.Transcript(
            ac='NM_001097.3',
            origin=o1,
            hgnc='ACR',
            cds_start_i=0,
            cds_end_i=1,
            cds_md5='a',
        )
        t2 = usam.Transcript(
            ac='NM_001098.3',
            origin=o1,
            hgnc='ACO2',
            cds_start_i=2,
            cds_end_i=3,
            cds_md5='b',
        )
        t3 = usam.Transcript(
            ac='DummyTx',
            origin=o2,
            hgnc='DummyGene',
            cds_start_i=4,
            cds_end_i=5,
            cds_md5='c',
        )
        self.session.add(t1)
        self.session.add(t2)
        self.session.add(t3)

        self.session.commit()

        # cf = configparser.ConfigParser()
        # cf.add_section('uta')
        # cf.set('uta', 'admin_role', 'uta_admin')

        ul.load_assoc_ac(self.session, {"FILE": "tests/data/assocacs.gz"}, None)

        # check associated_accessions table
        aa = self.session.query(usam.AssociatedAccessions).order_by(usam.AssociatedAccessions.tx_ac).all()
        aa_list = [{'tx_ac': aa.tx_ac, 'pro_ac': aa.pro_ac, 'origin_name': aa.origin.name} for aa in aa]
        expected_aa_list = [
            {
                'tx_ac': 'DummyTx',
                'pro_ac': 'DummyProtein',
                'origin_name': 'DummyOrigin',
            },
            {
                'tx_ac': 'NM_001097.3',
                'pro_ac': 'NP_001088.2',
                'origin_name': 'NCBI',
            },
            {
                'tx_ac': 'NM_001098.3',
                'pro_ac': 'NP_001089.1',
                'origin_name': 'NCBI',
            },
        ]
        self.assertEqual(aa_list, expected_aa_list)
        breakpoint()
