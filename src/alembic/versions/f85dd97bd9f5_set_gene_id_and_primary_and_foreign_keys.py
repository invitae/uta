"""set gene_id and primary and foreign keys

Revision ID: f85dd97bd9f5
Revises: 595a586e6de7
Create Date: 2024-04-10 22:14:14.055461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f85dd97bd9f5'
down_revision: Union[str, None] = '595a586e6de7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "gene", "gene_id", existing_type=sa.TEXT(), nullable=False, schema="uta"
    )
    op.create_primary_key("gene_pkey", "gene", ["gene_id"], schema="uta")
    op.create_index(op.f("ix_uta_gene_hgnc"), "gene", ["hgnc"], unique=False, schema="uta")
    op.alter_column(
        "transcript", "gene_id", existing_type=sa.TEXT(), nullable=False, schema="uta"
    )
    op.create_index(
        op.f("ix_uta_transcript_gene_id"),
        "transcript",
        ["gene_id"],
        unique=False,
        schema="uta",
    )
    op.create_foreign_key(
        "fk_uta_transcript_gene_gene_id",
        "transcript",
        "gene",
        ["gene_id"],
        ["gene_id"],
        source_schema="uta",
        referent_schema="uta",
        onupdate="RESTRICT",
        ondelete="RESTRICT",
    )
    # ### end Alembic commands ###

    # ### handle first part of hgnc -> gene_symbol column rename ###
    op.add_column("gene", sa.Column("symbol", sa.Text(), nullable=True), schema="uta")
    op.create_index(op.f("ix_uta_gene_symbol"), "gene", ["symbol"], unique=False, schema="uta")
    op.execute("UPDATE gene SET symbol = hgnc;")
    # ### end of hgnc -> gene_symbol column rename ###

    # ### updates required to existing views needed to drop hgnc from transcript. ###
    op.execute("DROP VIEW IF EXISTS tx_similarity_v CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tx_def_summary_mv CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_def_summary_dv CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tx_exon_set_summary_mv CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_exon_set_summary_dv CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_exon_aln_v CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_alt_exon_pairs_v CASCADE;")
    op.execute("DROP VIEW IF EXISTS _discontiguous_tx CASCADE;")
    op.execute("""
            CREATE VIEW _discontiguous_tx AS 
                SELECT g.symbol,
                g.symbol as hgnc,
                g.gene_id,
                es.exon_set_id,
                es.tx_ac,
                format('[%s-%s]'::text, e1.end_i, e2.start_i) AS gap,
                e1.exon_id AS e1_exon_id,
                e1.ord AS e1_ord,
                e1.start_i AS e1_start_i,
                e1.end_i AS e1_end_i,
                e2.exon_id AS e2_exon_id,
                e2.ord AS e2_ord,
                e2.start_i AS e2_start_i,
                e2.end_i AS e2_end_i
               FROM exon_set es
                 JOIN transcript t ON es.tx_ac = t.ac
                 JOIN gene as g ON t.gene_id = g.gene_id
                 JOIN exon e1 ON es.exon_set_id = e1.exon_set_id
                 JOIN exon e2 ON es.exon_set_id = e2.exon_set_id AND e2.ord = (e1.ord + 1) AND e1.end_i <> e2.start_i
              WHERE es.alt_aln_method = 'transcript'::text;
        """)
    op.execute("""
            CREATE VIEW tx_alt_exon_pairs_v AS
                SELECT g.symbol, g.symbol as hgnc, g.gene_id,TES.exon_SET_id AS tes_exon_SET_id,
                   AES.exon_SET_id AS aes_exon_SET_id, TES.tx_ac AS tx_ac,AES.alt_ac AS alt_ac,
                   AES.alt_strand,AES.alt_aln_method, TEX.ORD AS ORD,TEX.exon_id AS tx_exon_id,
                   AEX.exon_id AS alt_exon_id, TEX.start_i AS tx_start_i,TEX.END_i AS tx_END_i, 
                   AEX.start_i AS alt_start_i, AEX.END_i AS alt_END_i, EA.exon_aln_id,EA.cigar
                FROM exon_SET tes
                JOIN transcript t ON tes.tx_ac=t.ac
                JOIN gene g ON t.gene_id=g.gene_id
                JOIN exon_set aes ON tes.tx_ac=aes.tx_ac AND tes.alt_aln_method='transcript' AND aes.alt_aln_method!='transcript'
                JOIN exon tex ON tes.exon_SET_id=tex.exon_SET_id
                JOIN exon aex ON aes.exon_SET_id=aex.exon_SET_id AND tex.ORD=aex.ORD
                LEFT JOIN exon_aln ea ON ea.tx_exon_id=tex.exon_id AND ea.alt_exon_id=AEX.exon_id;
        """)
    op.execute("""
            CREATE VIEW tx_exon_aln_v AS 
                SELECT G.symbol, G.symbol AS hgnc, G.gene_id, T.ac as tx_ac, AES.alt_ac,
                       AES.alt_aln_method,AES.alt_strand, TE.ord, TE.start_i as tx_start_i,
                       TE.end_i as tx_end_i, AE.start_i as alt_start_i, AE.end_i as alt_end_i,
                       EA.cigar, EA.tx_aseq, EA.alt_aseq, TES.exon_set_id AS tx_exon_set_id,
                       AES.exon_set_id as alt_exon_set_id, TE.exon_id as tx_exon_id, 
                       AE.exon_id as alt_exon_id, EA.exon_aln_id
                FROM transcript T
                JOIN gene G ON T.gene_id=G.gene_id
                JOIN exon_set TES ON T.ac=TES.tx_ac AND TES.alt_aln_method ='transcript'
                JOIN exon_set AES on T.ac=AES.tx_ac and AES.alt_aln_method!='transcript'
                JOIN exon TE ON TES.exon_set_id=TE.exon_set_id
                JOIN exon AE ON AES.exon_set_id=AE.exon_set_id AND TE.ord=AE.ord
                LEFT JOIN exon_aln EA ON TE.exon_id=EA.tx_exon_id AND AE.exon_id=EA.alt_exon_id;
        """)
    op.execute("""
            CREATE VIEW tx_exon_set_summary_dv AS
                SELECT G.symbol, G.symbol as hgnc, G.gene_id, cds_md5, es_fingerprint, tx_ac, alt_ac, 
                       alt_aln_method, alt_strand, exon_set_id, n_exons, se_i, starts_i, ends_i, lengths
                FROM transcript T
                JOIN gene G ON T.gene_id=G.gene_id
                JOIN exon_set_exons_fp_mv ESE ON T.ac=ESE.tx_ac;
        """)
    op.execute("""
            CREATE MATERIALIZED VIEW tx_exon_set_summary_mv AS SELECT * FROM tx_exon_set_summary_dv WITH NO DATA;
            CREATE INDEX tx_exon_set_summary_mv_cds_md5_ix ON tx_exon_set_summary_mv(cds_md5);
            CREATE INDEX tx_exon_set_summary_mv_es_fingerprint_ix ON tx_exon_set_summary_mv(es_fingerprint);
            CREATE INDEX tx_exon_set_summary_mv_tx_ac_ix ON tx_exon_set_summary_mv(tx_ac);
            CREATE INDEX tx_exon_set_summary_mv_alt_ac_ix ON tx_exon_set_summary_mv(alt_ac);
            CREATE INDEX tx_exon_set_summary_mv_alt_aln_method_ix ON tx_exon_set_summary_mv(alt_aln_method);
            GRANT SELECT ON tx_exon_set_summary_mv TO public;
            REFRESH MATERIALIZED VIEW tx_exon_set_summary_mv;
        """)
    op.execute("""
            CREATE VIEW tx_def_summary_dv AS
                SELECT TESS.exon_set_id, TESS.tx_ac, TESS.alt_ac, TESS.alt_aln_method, TESS.alt_strand,
                       TESS.symbol, TESS.hgnc, TESS.gene_id, TESS.cds_md5, TESS.es_fingerprint, CEF.cds_es_fp, 
                       CEF.cds_exon_lengths_fp, TESS.n_exons, TESS.se_i, CEF.cds_se_i, TESS.starts_i, 
                       TESS.ends_i, TESS.lengths, T.cds_start_i, T.cds_end_i, CEF.cds_start_exon, CEF.cds_end_exon
                FROM tx_exon_set_summary_mv TESS
                JOIN transcript T ON TESS.tx_ac=T.ac
                LEFT JOIN _cds_exons_fp_v CEF ON TESS.exon_set_id=CEF.exon_set_id
                WHERE TESS.alt_aln_method = 'transcript';
        """)
    op.execute("""
            CREATE MATERIALIZED VIEW tx_def_summary_mv AS SELECT * FROM tx_def_summary_dv WITH NO DATA;
            CREATE INDEX tx_def_summary_mv_tx_ac ON tx_def_summary_mv (tx_ac);
            CREATE INDEX tx_def_summary_mv_alt_ac ON tx_def_summary_mv (alt_ac);
            CREATE INDEX tx_def_summary_mv_alt_aln_method ON tx_def_summary_mv (alt_aln_method);
            CREATE INDEX tx_def_summary_mv_hgnc ON tx_def_summary_mv (hgnc);
            CREATE INDEX tx_def_summary_mv_symbol ON tx_def_summary_mv (symbol);
            CREATE INDEX tx_def_summary_mv_gene_id ON tx_def_summary_mv (gene_id);
            REFRESH MATERIALIZED VIEW tx_def_summary_mv;
        """)
    op.execute("""
        CREATE VIEW tx_similarity_v AS
        SELECT DISTINCT
               D1.tx_ac as tx_ac1, D2.tx_ac as tx_ac2,
               D1.symbol = D2.symbol as symbol_eq,
               D1.cds_md5=D2.cds_md5 as cds_eq,
               D1.es_fingerprint=D2.es_fingerprint as es_fp_eq,
               D1.cds_es_fp=D2.cds_es_fp as cds_es_fp_eq,
               D1.cds_exon_lengths_fp=D2.cds_exon_lengths_fp as cds_exon_lengths_fp_eq
        FROM tx_def_summary_mv D1
        JOIN tx_def_summary_mv D2 on (D1.tx_ac != D2.tx_ac
                                      and (D1.symbol=D2.symbol
                                           or D1.cds_md5=D2.cds_md5
                                           or D1.es_fingerprint=D2.es_fingerprint
                                           or D1.cds_es_fp=D2.cds_es_fp
                                           or D1.cds_exon_lengths_fp=D2.cds_exon_lengths_fp
                                           ));
    """)
    # ### end of updates to existing views ###

    # ### drop hgnc from transcript ###
    op.drop_column('transcript', 'hgnc', schema='uta')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### updates to views to add hgnc to transcript ###
    op.add_column('transcript', sa.Column('hgnc', sa.Text(), nullable=True), schema='uta')
    # ### end of updates to transcript ###

    # ### commands to downgrade views before adding hgnc to transcript ###
    op.execute("DROP VIEW IF EXISTS tx_similarity_v CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tx_def_summary_mv CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_def_summary_dv CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS tx_exon_set_summary_mv CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_exon_set_summary_dv CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_exon_aln_v CASCADE;")
    op.execute("DROP VIEW IF EXISTS tx_alt_exon_pairs_v CASCADE;")
    op.execute("DROP VIEW IF EXISTS _discontiguous_tx CASCADE;")
    op.execute("""
            CREATE VIEW _discontiguous_tx AS 
                SELECT t.hgnc,
                es.exon_set_id,
                es.tx_ac,
                format('[%s-%s]'::text, e1.end_i, e2.start_i) AS gap,
                e1.exon_id AS e1_exon_id,
                e1.ord AS e1_ord,
                e1.start_i AS e1_start_i,
                e1.end_i AS e1_end_i,
                e2.exon_id AS e2_exon_id,
                e2.ord AS e2_ord,
                e2.start_i AS e2_start_i,
                e2.end_i AS e2_end_i
               FROM exon_set es
                 JOIN transcript t ON es.tx_ac = t.ac
                 JOIN exon e1 ON es.exon_set_id = e1.exon_set_id
                 JOIN exon e2 ON es.exon_set_id = e2.exon_set_id AND e2.ord = (e1.ord + 1) AND e1.end_i <> e2.start_i
              WHERE es.alt_aln_method = 'transcript'::text;
        """)
    op.execute("""
            CREATE VIEW tx_alt_exon_pairs_v AS
                SELECT t.hgnc,TES.exon_SET_id AS tes_exon_SET_id,AES.exon_SET_id AS aes_exon_SET_id,
                   TES.tx_ac AS tx_ac,AES.alt_ac AS alt_ac,AES.alt_strand,AES.alt_aln_method,
                   TEX.ORD AS ORD,TEX.exon_id AS tx_exon_id,AEX.exon_id AS alt_exon_id,
                   TEX.start_i AS tx_start_i,TEX.END_i AS tx_END_i, AEX.start_i AS alt_start_i,AEX.END_i AS alt_END_i,
                   EA.exon_aln_id,EA.cigar
                FROM exon_SET tes
                JOIN transcript t ON tes.tx_ac=t.ac
                JOIN exon_set aes ON tes.tx_ac=aes.tx_ac AND tes.alt_aln_method='transcript' AND aes.alt_aln_method!='transcript'
                JOIN exon tex ON tes.exon_SET_id=tex.exon_SET_id
                JOIN exon aex ON aes.exon_SET_id=aex.exon_SET_id AND tex.ORD=aex.ORD
                LEFT JOIN exon_aln ea ON ea.tx_exon_id=tex.exon_id AND ea.alt_exon_id=AEX.exon_id;
        """)
    op.execute("""
                CREATE VIEW tx_exon_aln_v AS 
                    SELECT T.hgnc,T.ac as tx_ac,AES.alt_ac,AES.alt_aln_method,AES.alt_strand,
                           TE.ord, TE.start_i as tx_start_i,TE.end_i as tx_end_i,
                           AE.start_i as alt_start_i, AE.end_i as alt_end_i,
                           EA.cigar, EA.tx_aseq, EA.alt_aseq,
                           TES.exon_set_id AS tx_exon_set_id,AES.exon_set_id as alt_exon_set_id,
                           TE.exon_id as tx_exon_id, AE.exon_id as alt_exon_id,
                           EA.exon_aln_id
                    FROM transcript T
                    JOIN exon_set TES ON T.ac=TES.tx_ac AND TES.alt_aln_method ='transcript'
                    JOIN exon_set AES on T.ac=AES.tx_ac and AES.alt_aln_method!='transcript'
                    JOIN exon TE ON TES.exon_set_id=TE.exon_set_id
                    JOIN exon AE ON AES.exon_set_id=AE.exon_set_id AND TE.ord=AE.ord
                    LEFT JOIN exon_aln EA ON TE.exon_id=EA.tx_exon_id AND AE.exon_id=EA.alt_exon_id;
            """)
    op.execute("""
                CREATE VIEW tx_exon_set_summary_dv AS
                    SELECT T.hgnc,cds_md5,es_fingerprint,tx_ac,alt_ac,alt_aln_method,alt_strand,exon_set_id,n_exons,se_i,starts_i,ends_i,lengths
                    FROM transcript T
                    JOIN exon_set_exons_fp_mv ESE ON T.ac=ESE.tx_ac;
            """)
    op.execute("""
            CREATE MATERIALIZED VIEW tx_exon_set_summary_mv AS SELECT * FROM tx_exon_set_summary_dv WITH NO DATA;
            CREATE INDEX tx_exon_set_summary_mv_cds_md5_ix ON tx_exon_set_summary_mv(cds_md5);
            CREATE INDEX tx_exon_set_summary_mv_es_fingerprint_ix ON tx_exon_set_summary_mv(es_fingerprint);
            CREATE INDEX tx_exon_set_summary_mv_tx_ac_ix ON tx_exon_set_summary_mv(tx_ac);
            CREATE INDEX tx_exon_set_summary_mv_alt_ac_ix ON tx_exon_set_summary_mv(alt_ac);
            CREATE INDEX tx_exon_set_summary_mv_alt_aln_method_ix ON tx_exon_set_summary_mv(alt_aln_method);
            GRANT SELECT ON tx_exon_set_summary_mv TO public;
            REFRESH MATERIALIZED VIEW tx_exon_set_summary_mv;
        """)
    op.execute("""
                CREATE VIEW tx_def_summary_dv AS
                    SELECT TESS.exon_set_id, TESS.tx_ac, TESS.alt_ac, TESS.alt_aln_method, TESS.alt_strand,
                           TESS.hgnc, TESS.cds_md5, TESS.es_fingerprint, CEF.cds_es_fp, 
                           CEF.cds_exon_lengths_fp, TESS.n_exons, TESS.se_i, CEF.cds_se_i, TESS.starts_i, 
                           TESS.ends_i, TESS.lengths, T.cds_start_i, T.cds_end_i, CEF.cds_start_exon, CEF.cds_end_exon
                    FROM tx_exon_set_summary_mv TESS
                    JOIN transcript T ON TESS.tx_ac=T.ac
                    LEFT JOIN _cds_exons_fp_v CEF ON TESS.exon_set_id=CEF.exon_set_id
                    WHERE TESS.alt_aln_method = 'transcript';
            """)
    op.execute("""
                CREATE MATERIALIZED VIEW tx_def_summary_mv AS SELECT * FROM tx_def_summary_dv WITH NO DATA;
                CREATE INDEX tx_def_summary_mv_tx_ac ON tx_def_summary_mv (tx_ac);
                CREATE INDEX tx_def_summary_mv_alt_ac ON tx_def_summary_mv (alt_ac);
                CREATE INDEX tx_def_summary_mv_alt_aln_method ON tx_def_summary_mv (alt_aln_method);
                CREATE INDEX tx_def_summary_mv_hgnc ON tx_def_summary_mv (hgnc);
                REFRESH MATERIALIZED VIEW tx_def_summary_mv;
            """)
    op.execute("""
    CREATE VIEW tx_similarity_v AS
    SELECT DISTINCT
           D1.tx_ac as tx_ac1, D2.tx_ac as tx_ac2,
           D1.hgnc = D2.hgnc as hgnc_eq,
           D1.cds_md5=D2.cds_md5 as cds_eq,
           D1.es_fingerprint=D2.es_fingerprint as es_fp_eq,
           D1.cds_es_fp=D2.cds_es_fp as cds_es_fp_eq,
           D1.cds_exon_lengths_fp=D2.cds_exon_lengths_fp as cds_exon_lengths_fp_eq
    FROM tx_def_summary_mv D1
    JOIN tx_def_summary_mv D2 on (D1.tx_ac != D2.tx_ac
                                  and (D1.hgnc=D2.hgnc
                                       or D1.cds_md5=D2.cds_md5
                                       or D1.es_fingerprint=D2.es_fingerprint
                                       or D1.cds_es_fp=D2.cds_es_fp
                                       or D1.cds_exon_lengths_fp=D2.cds_exon_lengths_fp
                                       ));
    """)
    # ### end of updates to views ###

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_uta_transcript_gene_gene_id", "transcript", schema="uta", type_="foreignkey")
    op.drop_index(op.f("ix_uta_transcript_gene_id"), table_name="transcript", schema="uta")
    op.alter_column("transcript", "gene_id",
               existing_type=sa.TEXT(),
               nullable=True,
               schema="uta")
    op.drop_index(op.f("ix_uta_gene_hgnc"), table_name="gene", schema="uta")
    op.drop_constraint("gene_pkey", "gene", schema="uta")
    op.alter_column("gene", "gene_id",
               existing_type=sa.TEXT(),
               nullable=True,
               schema="uta")
    op.drop_index(op.f("ix_uta_gene_symbol"), table_name="gene", schema="uta")
    op.drop_column("gene", "symbol", schema="uta")
    # ### end Alembic commands ###
