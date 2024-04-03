"""initial version of UTA schema 1.1

Revision ID: 1b8f087cc856
Revises: 
Create Date: 2015-08-21 10:53:50.666152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b8f087cc856'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('associated_accessions',
    sa.Column('associated_accession_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tx_ac', sa.Text(), nullable=False),
    sa.Column('pro_ac', sa.Text(), nullable=False),
    sa.Column('origin', sa.Text(), nullable=False),
    sa.Column('added', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('associated_accession_id'),
    schema='uta_1_1'
    )
    op.create_index('associated_accessions_pro_ac', 'associated_accessions', ['pro_ac'], unique=False, schema='uta_1_1')
    op.create_index('associated_accessions_tx_ac', 'associated_accessions', ['tx_ac'], unique=False, schema='uta_1_1')
    op.create_index('unique_pair_in_origin', 'associated_accessions', ['origin', 'tx_ac', 'pro_ac'], unique=True, schema='uta_1_1')
    op.create_table('gene',
    sa.Column('hgnc', sa.Text(), nullable=False),
    sa.Column('maploc', sa.Text(), nullable=True),
    sa.Column('descr', sa.Text(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('aliases', sa.Text(), nullable=True),
    sa.Column('added', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('hgnc'),
    schema='uta_1_1'
    )
    op.create_table('meta',
    sa.Column('key', sa.Text(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('key'),
    schema='uta_1_1'
    )
    op.create_table('origin',
    sa.Column('origin_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('descr', sa.Text(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('url', sa.Text(), nullable=True),
    sa.Column('url_ac_fmt', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('origin_id'),
    sa.UniqueConstraint('name'),
    schema='uta_1_1'
    )
    op.create_table('seq',
    sa.Column('seq_id', sa.Text(), nullable=False),
    sa.Column('len', sa.Integer(), nullable=False),
    sa.Column('seq', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('seq_id'),
    schema='uta_1_1'
    )
    op.create_table('seq_anno',
    sa.Column('seq_anno_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('seq_id', sa.Text(), nullable=True),
    sa.Column('origin_id', sa.Integer(), nullable=False),
    sa.Column('ac', sa.Text(), nullable=False),
    sa.Column('descr', sa.Text(), nullable=True),
    sa.Column('added', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['origin_id'], ['uta_1_1.origin.origin_id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['seq_id'], ['uta_1_1.seq.seq_id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('seq_anno_id'),
    schema='uta_1_1'
    )
    op.create_index(op.f('ix_uta_1_1_seq_anno_ac'), 'seq_anno', ['ac'], unique=False, schema='uta_1_1')
    op.create_index(op.f('ix_uta_1_1_seq_anno_seq_id'), 'seq_anno', ['seq_id'], unique=False, schema='uta_1_1')
    op.create_index('seq_anno_ac_unique_in_origin', 'seq_anno', ['origin_id', 'ac'], unique=True, schema='uta_1_1')
    op.create_table('transcript',
    sa.Column('ac', sa.Text(), nullable=False),
    sa.Column('origin_id', sa.Integer(), nullable=False),
    sa.Column('hgnc', sa.Text(), nullable=True),
    sa.Column('cds_start_i', sa.Integer(), nullable=True),
    sa.Column('cds_end_i', sa.Integer(), nullable=True),
    sa.Column('cds_md5', sa.Text(), nullable=True),
    sa.Column('added', sa.DateTime(), nullable=False),
    sa.CheckConstraint('cds_start_i <= cds_end_i', name='cds_start_i_must_be_le_cds_end_i'),
    sa.ForeignKeyConstraint(['origin_id'], ['uta_1_1.origin.origin_id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('ac'),
    schema='uta_1_1'
    )
    op.create_index(op.f('ix_uta_1_1_transcript_cds_md5'), 'transcript', ['cds_md5'], unique=False, schema='uta_1_1')
    op.create_index(op.f('ix_uta_1_1_transcript_origin_id'), 'transcript', ['origin_id'], unique=False, schema='uta_1_1')
    op.create_table('exon_set',
    sa.Column('exon_set_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tx_ac', sa.Text(), nullable=False),
    sa.Column('alt_ac', sa.Text(), nullable=False),
    sa.Column('alt_strand', sa.SmallInteger(), nullable=False),
    sa.Column('alt_aln_method', sa.Text(), nullable=False),
    sa.Column('added', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['tx_ac'], ['uta_1_1.transcript.ac'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('exon_set_id'),
    sa.UniqueConstraint('tx_ac', 'alt_ac', 'alt_aln_method', name='<transcript,reference,method> must be unique'),
    schema='uta_1_1'
    )
    op.create_table('exon',
    sa.Column('exon_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('exon_set_id', sa.Integer(), nullable=False),
    sa.Column('start_i', sa.Integer(), nullable=False),
    sa.Column('end_i', sa.Integer(), nullable=False),
    sa.Column('ord', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.CheckConstraint('start_i < end_i', name='exon_start_i_must_be_lt_end_i'),
    sa.ForeignKeyConstraint(['exon_set_id'], ['uta_1_1.exon_set.exon_set_id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('exon_id'),
    sa.UniqueConstraint('exon_set_id', 'end_i', name='end_i_must_be_unique_in_exon_set'),
    sa.UniqueConstraint('exon_set_id', 'start_i', name='start_i_must_be_unique_in_exon_set'),
    schema='uta_1_1'
    )
    op.create_index(op.f('ix_uta_1_1_exon_exon_set_id'), 'exon', ['exon_set_id'], unique=False, schema='uta_1_1')
    op.create_table('exon_aln',
    sa.Column('exon_aln_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tx_exon_id', sa.Integer(), nullable=False),
    sa.Column('alt_exon_id', sa.Integer(), nullable=False),
    sa.Column('cigar', sa.Text(), nullable=False),
    sa.Column('added', sa.DateTime(), nullable=False),
    sa.Column('tx_aseq', sa.Text(), nullable=False),
    sa.Column('alt_aseq', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['alt_exon_id'], ['uta_1_1.exon.exon_id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tx_exon_id'], ['uta_1_1.exon.exon_id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('exon_aln_id'),
    schema='uta_1_1'
    )
    op.create_index(op.f('ix_uta_1_1_exon_aln_alt_exon_id'), 'exon_aln', ['alt_exon_id'], unique=False, schema='uta_1_1')
    op.create_index(op.f('ix_uta_1_1_exon_aln_tx_exon_id'), 'exon_aln', ['tx_exon_id'], unique=False, schema='uta_1_1')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_uta_1_1_exon_aln_tx_exon_id'), table_name='exon_aln', schema='uta_1_1')
    op.drop_index(op.f('ix_uta_1_1_exon_aln_alt_exon_id'), table_name='exon_aln', schema='uta_1_1')
    op.drop_table('exon_aln', schema='uta_1_1')
    op.drop_index(op.f('ix_uta_1_1_exon_exon_set_id'), table_name='exon', schema='uta_1_1')
    op.drop_table('exon', schema='uta_1_1')
    op.drop_table('exon_set', schema='uta_1_1')
    op.drop_index(op.f('ix_uta_1_1_transcript_origin_id'), table_name='transcript', schema='uta_1_1')
    op.drop_index(op.f('ix_uta_1_1_transcript_cds_md5'), table_name='transcript', schema='uta_1_1')
    op.drop_table('transcript', schema='uta_1_1')
    op.drop_index('seq_anno_ac_unique_in_origin', table_name='seq_anno', schema='uta_1_1')
    op.drop_index(op.f('ix_uta_1_1_seq_anno_seq_id'), table_name='seq_anno', schema='uta_1_1')
    op.drop_index(op.f('ix_uta_1_1_seq_anno_ac'), table_name='seq_anno', schema='uta_1_1')
    op.drop_table('seq_anno', schema='uta_1_1')
    op.drop_table('seq', schema='uta_1_1')
    op.drop_table('origin', schema='uta_1_1')
    op.drop_table('meta', schema='uta_1_1')
    op.drop_table('gene', schema='uta_1_1')
    op.drop_index('unique_pair_in_origin', table_name='associated_accessions', schema='uta_1_1')
    op.drop_index('associated_accessions_tx_ac', table_name='associated_accessions', schema='uta_1_1')
    op.drop_index('associated_accessions_pro_ac', table_name='associated_accessions', schema='uta_1_1')
    op.drop_table('associated_accessions', schema='uta_1_1')
    # ### end Alembic commands ###
