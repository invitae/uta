from __future__ import absolute_import, division, print_function, unicode_literals

from configparser import ConfigParser
import csv
import datetime
import gzip
import hashlib
import itertools
import logging
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

from biocommons.seqrepo import SeqRepo
from bioutils.coordinates import strand_pm_to_int, MINUS_STRAND
from bioutils.digests import seq_md5
from bioutils.sequences import reverse_complement, translate_cds
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import or_, text
import psycopg2.extras
import six
from uta_align.align.algorithms import cigar_alignment, needleman_wunsch_gotoh_align

from uta.lru_cache import lru_cache

import uta
import uta.formats.exonset as ufes
import uta.formats.geneinfo as ufgi
import uta.formats.seqinfo as ufsi
import uta.formats.txinfo as ufti
import uta.parsers.geneinfo
import uta.parsers.seqgene
from uta.exceptions import ExonStructureMismatchError

usam = uta.models

logger = logging.getLogger(__name__)

def align_exons(session, opts, cf):
    # N.B. setup.py declares dependencies for using uta as a client.  The
    # imports below are loading depenencies only and are not in setup.py.

    update_period = 1000

    def _get_cursor(con):
        cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        cur.execute("set role {admin_role};".format(
            admin_role=cf.get("uta", "admin_role")))
        cur.execute("set search_path = " + usam.schema_name)
        return cur

    def align(s1, s2):
        score, cigar = needleman_wunsch_gotoh_align(s1.encode("ascii"),
                                                    s2.encode("ascii"),
                                                    extended_cigar=True)
        tx_aseq, alt_aseq = cigar_alignment(
            tx_seq, alt_seq, cigar, hide_match=False)
        return tx_aseq.decode("ascii"), alt_aseq.decode("ascii"), cigar.to_string().decode("ascii")

    aln_sel_sql = """
    SELECT * FROM tx_alt_exon_pairs_v TAEP
    WHERE exon_aln_id is NULL and tx_ac !~ '/'
    ORDER BY tx_ac, alt_ac
    """

    aln_ins_sql = """
    INSERT INTO exon_aln (tx_exon_id,alt_exon_id,cigar,added)
    VALUES (%s,%s,%s,%s)
    """

    con = session.bind.pool.connect()
    cur = _get_cursor(con)
    cur.execute(aln_sel_sql)
    n_rows = cur.rowcount

    if n_rows == 0:
        return

    logger.info("{} exon pairs to align".format(n_rows))

    sf = _get_seqfetcher(cf)

    def _fetch_seq(ac, s, e):
        logger.debug("fetching sequence {ac}[{s}:{e}]".format(ac=ac,s=s,e=e))
        seq = sf.fetch(ac,s,e)
        assert seq is not None, "sequence {ac}[{s}:{e}] should never be None (coordinates bogus?)".format(ac=ac,s=s,e=e)
        if isinstance(seq, six.binary_type):
            seq = seq.decode("ascii")  # force into unicode
        assert isinstance(seq, six.text_type)
        return seq

    rows = cur.fetchall()
    ac_warning = set()
    tx_acs = set()
    aln_rate_s = None
    decay_rate = 0.25
    n0, t0 = 0, time.time()

    for i_r, r in enumerate(rows):
        if i_r > 0 and (i_r % update_period == 0 or (i_r + 1) == n_rows):
            con.commit()

        if r.tx_ac in ac_warning or r.alt_ac in ac_warning:
            continue

        try:
            tx_seq = _fetch_seq(r.tx_ac, r.tx_start_i, r.tx_end_i)
        except KeyError:
            import IPython; IPython.embed()	  ### TODO: Remove IPython.embed()
            logger.warning(
                "{r.tx_ac}: Not in sequence sources; can't align".format(r=r))
            ac_warning.add(r.tx_ac)
            continue

        try:
            alt_seq = _fetch_seq(r.alt_ac, r.alt_start_i, r.alt_end_i)
        except KeyError:
            logger.warning(
                "{r.alt_ac}: Not in sequence sources; can't align".format(r=r))
            ac_warning.add(r.tx_ac)
            continue

        if r.alt_strand == MINUS_STRAND:
            alt_seq = reverse_complement(alt_seq)
        tx_seq = tx_seq.upper()
        alt_seq = alt_seq.upper()

        tx_aseq, alt_aseq, cigar_str = align(tx_seq, alt_seq)

        added = datetime.datetime.now()
        cur.execute(aln_ins_sql, [r.tx_exon_id, r.alt_exon_id, cigar_str, added])
        tx_acs.add(r.tx_ac)

        if i_r > 0 and (i_r % update_period == 0 or (i_r + 1) == n_rows):
            con.commit()
            n1, t1 = i_r, time.time()
            nd, td = n1 - n0, t1 - t0
            aln_rate = nd / td      # aln rate on this update period
            if aln_rate_s is None:  # aln_rate_s is EWMA smoothed average
                aln_rate_s = aln_rate
            else:
                aln_rate_s = decay_rate * aln_rate + (1.0 - decay_rate) * aln_rate_s
            etr = (n_rows - i_r - 1) / aln_rate_s        # etr in secs
            etr_s = str(datetime.timedelta(seconds=round(etr)))  # etr as H:M:S
            logger.info("{i_r}/{n_rows} {p_r:.1f}%; committed; speed={speed:.1f}/{speed_s:.1f} aln/sec (inst/emwa); etr={etr:.0f}s ({etr_s}); {n_tx} tx".format(
                i_r=i_r, n_rows=n_rows, p_r=i_r / n_rows * 100, speed=aln_rate, speed_s=aln_rate_s, etr=etr,
                etr_s=etr_s, n_tx=len(tx_acs)))
            tx_acs = set()
            n0, t0 = n1, t1

    cur.close()
    con.close()
    logger.info("{} distinct sequence accessions not found".format(len(ac_warning)))


def analyze(session, opts, cf):
    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))
    cmds = [
        "analyze verbose"
    ]
    for cmd in cmds:
        logger.info(cmd)
        session.execute(text(cmd))
    session.commit()


def check_transcripts(session: Session, opts: Dict, cf: ConfigParser):
    """
    Find transcripts in the given UTA database version which are not in the given txinfo file,
    and write those transcripts to the specified file.
    """
    # required opts
    txinfo_file = opts['TXINFO_FILE']
    uta_schema = opts['UTA_SCHEMA']
    output_file = opts['OUTPUT_FILE']

    # optional opts
    prefixes = opts.get('--prefixes')
    # prefixes should be comma-separated list
    transcript_prefixes = prefixes.split(',') if prefixes else None

    role = cf.get('uta', 'admin_role')
    session.execute(text(f"set role {role};"))
    session.execute(text(f"set search_path = {uta_schema};"))

    # fetch transcripts from uta
    Transcript = uta.models.Transcript
    query = session.query(Transcript)
    if transcript_prefixes:
        query = query.filter(or_(*[Transcript.ac.startswith(p) for p in transcript_prefixes]))
    query = query.with_entities(Transcript.ac)
    uta_transcripts = set(ac for (ac, ) in query)

    # subtract incoming txinfo transcripts
    txinfo_transcripts = set()
    with gzip.open(txinfo_file, 'rt') as txinfo_fp:
        for row in csv.DictReader(txinfo_fp, delimiter='\t'):
            txinfo_transcripts.add(row['ac'])
    result_transcripts = uta_transcripts - txinfo_transcripts

    # write difference to output file
    with open(output_file, 'wt') as output_fp:
        output_fp.writelines(f'{t}\n' for t in sorted(result_transcripts))


def check_transl_except(session, opts, cf):
    """
    Find transcripts in the given transcript file which are in the given UTA database version
    and do not have transl_except entries when they should.
    """
    # required opts
    transcript_file = opts['TRANSCRIPT_FILE']
    uta_schema = opts['UTA_SCHEMA']
    output_file = opts['OUTPUT_FILE']

    role = cf.get('uta', 'admin_role')
    session.execute(text(f"set role {role};"))
    session.execute(text(f"set search_path = {uta_schema};"))

    Transcript = uta.models.Transcript
    AssociatedAccessions = usam.AssociatedAccessions

    def transcript_iterator() -> Generator[Tuple[str, int, int, Optional[str]], None, None]:
        with open(transcript_file, 'rt') as transcript_fp:
            for line in transcript_fp:
                transcript_ac = line.strip()
                transcript = (
                    session.query(Transcript)
                    .filter(Transcript.ac == transcript_ac)
                    .with_entities(Transcript.ac, Transcript.cds_start_i, Transcript.cds_end_i)
                    .one()
                )
                try:
                    assoc_ac = (
                        session.query(AssociatedAccessions)
                        .filter(AssociatedAccessions.tx_ac == transcript.ac)
                        .with_entities(AssociatedAccessions.tx_ac, AssociatedAccessions.pro_ac)
                        .one()
                    )
                    protein_ac = assoc_ac.pro_ac
                except NoResultFound:
                    logger.warning(f'No NP for transcript: {transcript_ac}')
                    protein_ac = None

                yield transcript.ac, transcript.cds_start_i, transcript.cds_end_i, protein_ac

    result_transcripts = set()
    warning_transcripts = set()
    sf = _get_seqfetcher(cf)
    for i, (transcript_ac, transcript_cds_start_i, transcript_cds_end_i, protein_ac) in enumerate(transcript_iterator()):
        if i % 1000 == 0:
            print(f'Progress: {i}')

        if protein_ac is None:
            warning_transcripts.add(transcript_ac)
            continue

        try:
            transcript_seq = sf.fetch(transcript_ac, transcript_cds_start_i, transcript_cds_end_i)
        except:
            logger.warning(f'No sequence for transcript: {transcript_ac}')
            transcript_seq = None

        if transcript_seq is None:
            warning_transcripts.add(transcript_ac)
            continue

        translated_protein_seq = translate_cds(transcript_seq, full_codons=False, ter_symbol='X').rstrip('*')

        try:
            protein_seq = sf.fetch(protein_ac)
        except:
            logger.warning(f'NP has no sequence: {protein_ac}, {transcript_ac}')
            protein_seq = None

        if protein_seq is None:
            warning_transcripts.add(transcript_ac)
            continue

        if protein_seq != translated_protein_seq:
            result_transcripts.add(transcript_ac)

    with open(output_file, 'wt') as output_fp:
        output_fp.writelines(f'{t}\n' for t in sorted(result_transcripts))


def create_schema(session, opts, cf):
    """Create and populate initial schema"""
    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    if session.bind.name == "postgresql" and usam.use_schema:
        session.execute(text("create schema " + usam.schema_name))
        session.execute(text("set search_path = " + usam.schema_name))
        session.commit()

    usam.Base.metadata.create_all(session.bind)
    session.add(usam.Meta(key="schema_version", value=usam.schema_version))
    session.add(
        usam.Meta(key="created on", value=datetime.datetime.now().isoformat()))
    session.add(usam.Meta(key="uta version", value=uta.__version__))
    session.add(usam.Meta(
        key="license", value="CC-BY-SA (http://creativecommons.org/licenses/by-sa/4.0/deed.en_US"))
    session.commit()
    logger.info("created schema")


def update_meta_data(session, opts, cf):
    """Update Meta table with schema version"""
    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    # check if schema version is up-to-date
    md_schema_version = session.query(usam.Meta).filter_by(key="schema_version").one()
    if md_schema_version.value != usam.schema_version:
        logger.info(f"updating schema version from {md_schema_version.value} to {usam.schema_version}")
        md_schema_version.value = usam.schema_version
        session.commit()
    else:
        logger.info(f"schema version {md_schema_version.value} is already up-to-date")

    # set updated on
    md_updated_on = session.query(usam.Meta).filter_by(key="updated on").one_or_none()
    if md_updated_on is None:
        session.add(usam.Meta(key="updated on", value=datetime.datetime.now().isoformat()))
        session.commit()
        logger.info("added updated on")
    else:
        md_updated_on.value = datetime.datetime.now().isoformat()
        session.commit()
        logger.info("updated updated on")


def drop_schema(session, opts, cf):
    if session.bind.name == "postgresql" and usam.use_schema:
        session.execute(
            text("set role {admin_role};".format(admin_role=cf.get("uta", "admin_role"))))
        session.execute(text("set search_path = " + usam.schema_name))

        ddl = "drop schema if exists " + usam.schema_name + " cascade"
        session.execute(ddl)
        session.commit()
        logger.info(ddl)


def grant_permissions(session, opts, cf):
    schema = usam.schema_name

    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    cmds = [
        # alter db doesn't belong here, and probably better to avoid the implicit behevior this encourages
        # "alter database {db} set search_path = {schema}".format(db=cf.get("uta", "database"),schema=schema),
        "grant usage on schema " + schema + " to PUBLIC",
    ]

    sql = "select concat(schemaname,'.',tablename) as fqrn from pg_tables where schemaname='{schema}'".format(
        schema=schema)
    rows = list(session.execute(text(sql)))
    cmds += ["grant select on {fqrn} to PUBLIC".format(
        fqrn=row.fqrn) for row in rows]
    cmds += ["alter table {fqrn} owner to uta_admin".format(
        fqrn=row.fqrn) for row in rows]

    sql = "select concat(schemaname,'.',viewname) as fqrn from pg_views where schemaname='{schema}'".format(
        schema=schema)
    rows = list(session.execute(text(sql)))
    cmds += ["grant select on {fqrn} to PUBLIC".format(
        fqrn=row.fqrn) for row in rows]
    cmds += ["alter view {fqrn} owner to uta_admin".format(
        fqrn=row.fqrn) for row in rows]

    sql = "select concat(schemaname,'.',matviewname) as fqrn from pg_matviews where schemaname='{schema}'".format(
        schema=schema)
    rows = list(session.execute(text(sql)))
    cmds += ["grant select on {fqrn} to PUBLIC".format(
        fqrn=row.fqrn) for row in rows]
    cmds += ["alter materialized view {fqrn} owner to uta_admin".format(
        fqrn=row.fqrn) for row in rows]

    for cmd in sorted(cmds):
        logger.info(cmd)
        session.execute(text(cmd))
    session.commit()


def load_assoc_ac(session, opts, cf):
    """
    Insert rows into `associated_accessions` table in the UTA database,
    using data from a file written by sbin/assoc-acs-merge.
    """
    logger.info("load_assoc_ac")

    admin_role = cf.get("uta", "admin_role")
    session.execute(text(f"set role {admin_role};"))
    session.execute(text(f"set search_path = {usam.schema_name};"))
    fname = opts["FILE"]

    with gzip.open(fname, "rt") as fhandle:
        for file_row in csv.DictReader(fhandle, delimiter="\t"):
            row = {
                "origin": file_row["origin"],
                "pro_ac": file_row["pro_ac"],
                "tx_ac": file_row["tx_ac"],
            }
            aa, created = _get_or_insert(
                session=session,
                table=usam.AssociatedAccessions,
                row=row,
                row_identifier=('origin', 'tx_ac', 'pro_ac'),
            )
            if created:
                # If committing on every insert is too slow, we can
                # look into committing in batches like load_txinfo does.
                session.commit()
                logger.info(f"Added: {aa.tx_ac}, {aa.pro_ac}, {aa.origin}")
            else:
                logger.info(f"Already exists: {file_row}")
                # All fields should should match when unique identifiers match.
                # Discrepancies should be investigated.
                existing_row = {
                    "origin": aa.origin,
                    "pro_ac": aa.pro_ac,
                    "tx_ac": aa.tx_ac,
                }


def load_exonset(session, opts, cf):
    # exonsets and associated exons are loaded together

    update_period = 25

    session.execute(
        text("set role {admin_role};".format(admin_role=cf.get("uta", "admin_role")))
    )
    session.execute(text("set search_path = " + usam.schema_name))

    n_rows = len(gzip.open(opts["FILE"], "rt").readlines()) - 1
    esr = ufes.ExonSetReader(gzip.open(opts["FILE"], "rt"))
    logger.info("opened " + opts["FILE"])

    n_new = 0
    n_unchanged = 0
    n_deprecated = 0
    n_skipped = 0
    n_errors = 0
    for i_es, es in enumerate(esr):
        skipped = False
        try:
            # determine if alignment and transcript have the same exon structure
            tx_es = (
                session.query(usam.ExonSet)
                .filter(
                    usam.ExonSet.tx_ac == es.tx_ac,
                    usam.ExonSet.alt_ac == es.tx_ac,
                    usam.ExonSet.alt_aln_method == "transcript",
                )
                .one()
            )
            tx_exon_count = len(tx_es.exons_se_i())
            aln_exon_count = len(es.exons_se_i.split(";"))
            if tx_exon_count == aln_exon_count:
                n, o = _upsert_exon_set_record(
                    session, es.tx_ac, es.alt_ac, es.strand, es.method, es.exons_se_i
                )
                session.commit()
            else:
                raise ExonStructureMismatchError(
                    "Exon structure mismatch: {tx_exon_count} exons in transcript {es.tx_ac}; {aln_exon_count} in alignment {es.alt_ac}".format(
                        tx_exon_count=tx_exon_count,
                        aln_exon_count=aln_exon_count,
                        es=es,
                    )
                )
        except IntegrityError as e:
            logger.exception(e)
            session.rollback()
            n_errors += 1
        except NoResultFound as e:
            logger.exception(e)
            logger.warning("NoResultFound for transcript ExonSet: {es.tx_ac}".format(es=es))
            skipped = True
        except ExonStructureMismatchError as e:
            logger.exception(e)
            skipped = True
        else:
            (no) = (n is not None, o is not None)
            if no == (True, False):
                n_new += 1
            elif no == (True, True):
                n_deprecated += 1
            elif no == (False, True):
                n_unchanged += 1
        finally:
            if skipped:
                n_skipped += 1
            if i_es % update_period == 0 or i_es + 1 == n_rows:
                logger.info(
                    "{i_es}/{n_rows} {p:.1f}%; {n_new} new, {n_unchanged} unchanged, {n_deprecated} deprecated, {n_skipped} skipped, {n_errors} n_errors".format(
                        i_es=i_es,
                        n_rows=n_rows,
                        n_new=n_new,
                        n_unchanged=n_unchanged,
                        n_deprecated=n_deprecated,
                        n_skipped=n_skipped,
                        n_errors=n_errors,
                        p=(i_es + 1) / n_rows * 100,
                    )
                )

    session.commit()


def load_geneinfo(session, opts, cf):
    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    gir = ufgi.GeneInfoReader(gzip.open(opts["FILE"], 'rt'))
    logger.info("opened " + opts["FILE"])

    for i_gi, gi in enumerate(gir):
        session.merge(
            usam.Gene(
                gene_id=gi.gene_id,
                hgnc=gi.hgnc,
                symbol=gi.gene_symbol,
                maploc=gi.maploc,
                descr=gi.descr,
                summary=gi.summary,
                aliases=gi.aliases,
                type=gi.type,
                xrefs=gi.xrefs,
            ))
        logger.debug("Added {gi.gene_symbol}: {gi.gene_id} ({gi.summary})".format(gi=gi))
    session.commit()


def load_ncbi_seqgene(session, opts, cf):
    """
    import data as downloaded (by you) as from
    ftp.ncbi.nih.gov/genomes/MapView/Homo_sapiens/sequence/current/initial_release/seq_gene.md.gz
    """
    def _seqgene_recs_to_tx_info(ac, assy, recs):
        ti = {
            "ac": ac,
            "assy": assy,
            "strand": strand_pm_to_int(recs[0]["chr_orient"]),
            "gene_id": int(recs[0]["feature_id"].replace("GeneID:", "")) if "GeneID" in recs[0]["feature_id"] else None,
        }
        segs = [(r["feature_type"], int(r["chr_start"]) - 1, int(r["chr_stop"]))
                for r in recs]
        cds_seg_idxs = [i for i in range(len(segs)) if segs[i][0] == "CDS"]
        # merge UTR-CDS and CDS-UTR exons if end of first == start of second
        # prefer this over general adjacent exon merge in case of alignment artifacts
        # last exon
        ei = cds_seg_idxs[-1]
        ti["cds_end_i"] = segs[ei][2]
        if ei < len(segs) - 1:
            if segs[ei][2] == segs[ei + 1][1]:
                segs[ei:ei + 2] = [("M", segs[ei][1], segs[ei + 1][2])]
        # first exon
        ei = cds_seg_idxs[0]
        ti["cds_start_i"] = segs[ei][1]
        if ei > 0:
            if segs[ei - 1][2] == segs[ei][1]:
                segs[ei - 1:ei + 1] = [("M", segs[ei - 1][1], segs[ei][2])]
        ti["exon_se_i"] = [s[1:3] for s in segs]
        return ti


    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    o_refseq = session.query(usam.Origin).filter(
        usam.Origin.name == "NCBI RefSeq").one()

    sg_filter = lambda r: (r["transcript"].startswith("NM_")
                           and r["group_label"] == "GRCh37.p10-Primary Assembly"
                           and r["feature_type"] in ["CDS", "UTR"])
    sgparser = uta.parsers.seqgene.SeqGeneParser(gzip.open(opts["FILE"], 'rt'),
                                                 filter=sg_filter)
    slurp = sorted(list(sgparser),
                   key=lambda r: (r["transcript"], r["group_label"], r["chr_start"], r["chr_stop"]))
    for k, i in itertools.groupby(slurp, key=lambda r: (r["transcript"], r["group_label"])):
        ac, assy = k
        ti = _seqgene_recs_to_tx_info(ac, assy, list(i))

        resp = session.query(usam.Transcript).filter(usam.Transcript.ac == ac)
        if resp.count() == 0:
            t = usam.Transcript(ac=ac, origin=o_refseq, gene_id=ti["gene_id"])
            session.add(t)
        else:
            t = resp.one()

        es = usam.ExonSet(
            transcript_id=t.transcript_id,
            ref_nseq_id=99,
            strand=ti["strand"],
            cds_start_i=ti["cds_start_i"],
            cds_end_i=ti["cds_end_i"],
        )


def load_origin(session, opts, cf):
    """Add/merge data origins

    """

    def _none_if_empty(s):
        return None if s == "" else s

    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    orir = csv.DictReader(open(opts["FILE"]), delimiter='\t')
    for rec in orir:
        ori = usam.Origin(name=rec["name"],
                          descr=_none_if_empty(rec["descr"]),
                          url=_none_if_empty(rec["url"]),
                          url_ac_fmt=_none_if_empty(rec["url_ac_fmt"]),
                          )
        u_ori = session.query(usam.Origin).filter(
            usam.Origin.name == rec["name"]).first()
        if u_ori:
            ori.origin_id = u_ori.origin_id
            session.merge(ori)
        else:
            session.add(ori)
        logger.info("Merged {ori.name} ({ori.descr})".format(ori=ori))
    session.commit()


def load_seqinfo(session, opts, cf):
    """load Seq entries with accessions from fasta file
    """

    # TODO: load_seqinfo is horrifically slow (via sqlalchemy). There
    # must be a better way.

    update_period = 100

    # TODO: Don't store sequences in UTA
    # load sequences up to max_len in size
    # 2e6 was chosen empirically based on sizes of NMs, NGs, NWs, NTs, NCs
    max_len = int(2e6)


    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    n_rows = len(gzip.open(opts["FILE"]).readlines()) - 1

    sir = ufsi.SeqInfoReader(gzip.open(opts["FILE"], 'rt'))
    logger.info("opened " + opts["FILE"])

    sf = _get_seqfetcher(cf)

    _md5_seq_cache = {}
    def _upsert_seq(si):
        if si.md5 in _md5_seq_cache:
            return _md5_seq_cache[si.md5]

        u_seq = session.query(usam.Seq).filter(usam.Seq.seq_id == md5).first()
        if u_seq is None:
            seq = str(sf[si.ac]).upper()
            if int(si.len) != len(seq):
                raise RuntimeError("Expected a sequence of length {si.len} for {si.md5}; got length {len2} for {si.ac}; skipping".format(
                    si=si, len2=len(seq)))
            iseq = seq if len(seq) < max_len else None
            u_seq = usam.Seq(seq_id=si.md5, len=si.len, seq=iseq)
            session.add(u_seq)
        _md5_seq_cache[si.md5] = u_seq
        return _md5_seq_cache[si.md5]

    i_md5 = 0
    n_created = 0
    for md5, si_iter in itertools.groupby(sorted(sir, key=lambda si: si.md5),
                                          key=lambda si: si.md5):
        sis = list(si_iter)

        # if sequence doesn't exist in sequence table, make it
        # this is to satisfy a FK dependency, which should be reconsidered
        si = sis[0]
        try:
            u_seq = _upsert_seq(si)
        except RuntimeError as e:
            logger.exception(e)
            continue

        for si in sis:
            u_ori = session.query(usam.Origin).filter(
                usam.Origin.name == si.origin).one()
            u_seqanno = session.query(usam.SeqAnno).filter(
                usam.SeqAnno.origin_id == u_ori.origin_id,
                usam.SeqAnno.ac == si.ac).first()
            logger.debug("seq_anno({si.origin},{si.ac},{si.md5}) {st}".format(
                si=si, st="exists" if u_seqanno is not None else "doesn't exist"))
            if u_seqanno:
                # update descr, perhaps
                if u_seqanno.seq_id != si.md5:
                    raise RuntimeError("{si.origin}:{si.ac} for {si.md5}: accession already exists for {seq_id}".format(
                        si=si, seq_id=u_seqanno.seq_id))
                if si.descr and u_seqanno.descr != si.descr:
                    u_seqanno.descr = si.descr
                    session.merge(u_seqanno)
            else:
                # create the new annotation
                logger.debug("creating seq_anno({si.origin},{si.ac},{si.md5})".format(si=si))
                u_seqanno = usam.SeqAnno(origin_id=u_ori.origin_id, seq_id=si.md5,
                                         ac=si.ac, descr=si.descr)
                session.add(u_seqanno)
                n_created += 1

        i_md5 += 1
        if i_md5 % update_period == 1:
            logger.info("{n_created} annotations created/{i_md5} sequences seen ({p:.1f}%)/{n_rows} sequences total".format(
                n_created=n_created, i_md5=i_md5, n_rows=n_rows, md5=md5, p=i_md5 / n_rows * 100))
            session.commit()
    session.commit()


def load_sequences(session, opts, cf):

    # TODO: Don't store sequences in UTA
    # load sequences up to max_len in size
    # 2e6 was chosen empirically based on sizes of NMs, NGs, NWs, NTs, NCs
    max_len = int(2e6)

    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    sf = _get_seqfetcher(cf)

    # fetch accessions for given sequences
    sql = """
    select S.seq_id,S.len,array_agg(SA.ac order by SA.ac~'^ENST',SA.ac) as acs
    from seq S
    join seq_anno SA on S.seq_id=SA.seq_id
    where S.len <= {max_len} and S.seq is NULL
    group by S.seq_id,len
    """.format(max_len=max_len)

    def _fetch_first(acs):
        # try all accessions in acs, return sequence of first that returns a
        # sequence
        for ac in row["acs"]:
            try:
                return sf.fetch(ac)
            except KeyError:
                pass
        return None

    for row in session.execute(sql):
        seq = _fetch_first(row["acs"])
        if seq is None:
            logger.warn("No sequence found for {acs}".format(acs=row["acs"]))
            continue
        seq = seq.upper()
        if row["len"] != len(seq):
            logger.error("Expected a sequence of length {len} for {md5} ({acs}); got sequence of length {len2}".format(
                len=row["len"], md5=row["seq_id"], acs=row["acs"], len2=len(seq)))
            continue
        assert row["len"] == len(seq), "expected a sequence of length {len} for {md5} ({acs}); got length {len2}".format(
            len=row["len"], md5=row["seq_id"], acs=row["acs"], len2=len(seq))
        session.execute(usam.Seq.__table__.update().values(
            seq=seq).where(usam.Seq.seq_id == row["seq_id"]))
        logger.info("loaded sequence of length {len} for {md5} ({acs})".format(
            len=len(seq), md5=row["seq_id"], acs=row["acs"]))
        session.commit()


def load_sql(session, opts, cf):
    """Create views"""
    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    for fn in opts["FILES"]:
        logger.info("loading " + fn)
        session.execute(open(fn).read())
    session.commit()


def load_txinfo(session, opts, cf):
    self_aln_method = "transcript"
    update_period = 250
    sf = None                 # established on first use, below

    @lru_cache(maxsize=100)
    def _fetch_origin_by_name(name):
        try:
            ori = session.query(usam.Origin).filter(
                usam.Origin.name == name).one()
        except NoResultFound as e:
            logger.error("No origin for " + ti.origin)
            raise e
        return ori

    n_rows = len(gzip.open(opts["FILE"], 'rt').readlines()) - 1
    tir = ufti.TxInfoReader(gzip.open(opts["FILE"], 'rt'))
    logger.info("opened " + opts["FILE"])

    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    n_new = 0
    n_unchanged = 0
    n_cds_changed = 0
    n_exons_changed = 0

    for i_ti, ti in enumerate(tir):
        if ti.exons_se_i == "":
            logger.warning(ti.ac + ": no exons?!; skipping.")
            continue

        if ti.cds_se_i:
            cds_start_i, cds_end_i = map(int, ti.cds_se_i.split(","))
            codon_table = ti.codon_table
        else:
            cds_start_i = cds_end_i = None
            codon_table = None
            cds_md5 = None

        # 1. Fetch or make the Transcript record
        existing = session.query(usam.Transcript).filter(
            usam.Transcript.ac == ti.ac,
            )
        assert existing.count() <= 1, "Expected max 1 existing transcripts with accession {ti.ac}".format(ti=ti)

        u_tx = None

        if existing.count() == 1:
            u_tx = existing[0]
            if (u_tx.cds_start_i, u_tx.cds_end_i) != (cds_start_i, cds_end_i):
                u_tx.ac = "{u_tx.ac}/{u_tx.cds_start_i}..{u_tx.cds_end_i}".format(u_tx=u_tx)
                logger.warn("Transcript {ti.ac}: CDS coordinates changed!; renamed to {u_tx.ac}".format(ti=ti, u_tx=u_tx))
                session.flush()
                u_tx = None
                n_cds_changed += 1

            if ti.transl_except:
                # if the transl_except exists, make sure it exists in the database.
                te_list = _create_translation_exceptions(
                    transcript=ti.ac, transl_except_list=ti.transl_except.split(";")
                )
                for te_data in te_list:
                    te, created = _get_or_insert(
                        session=session,
                        table=usam.TranslationException,
                        row=te_data,
                        row_identifier=("tx_ac", "start_position", "end_position", "amino_acid"),
                    )
                    if created:
                        logger.info(
                            f"TranslationException added: {te.tx_ac}, {te.start_position}, {te.end_position}, {te.amino_acid}"
                        )
                    else:
                        logger.info(
                            f"TranslationException already exists: {te.tx_ac}, {te.start_position}, {te.end_position}, {te.amino_acid}"
                        )



        # state: u_tx is set if a transcript was found and was
        # unchanged, or None if 1) no such was found or 2) was found
        # and had updated CDS coords.
        if u_tx is None:
            ori = _fetch_origin_by_name(ti.origin)

            if ti.cds_se_i:
                if sf is None:
                    sf = _get_seqfetcher(cf)
                try:
                    cds_seq = sf.fetch(ti.ac, cds_start_i, cds_end_i)
                except KeyError:
                    raise Exception("{ac}: not in sequence database".format(ac=ti.ac))
                cds_md5 = seq_md5(cds_seq)
            else:
                cds_md5 = None

            assert (cds_start_i is not None) ^ (cds_md5 is None), "failed: cds_start_i is None i.f.f. cds_md5_is None"
            u_tx = usam.Transcript(
                ac=ti.ac,
                origin=ori,
                gene_id=ti.gene_id,
                cds_start_i=cds_start_i,
                cds_end_i=cds_end_i,
                cds_md5=cds_md5,
                codon_table=codon_table,
            )
            session.add(u_tx)

            if ti.transl_except:
                # if transl_except exists, it looks like this:
                # (pos:333..335,aa:Sec);(pos:1017,aa:TERM)
                transl_except_list = ti.transl_except.split(';')
                te_list = _create_translation_exceptions(transcript=ti.ac, transl_except_list=transl_except_list)
                for te in te_list:
                    session.add(usam.TranslationException(**te))

        if u_tx.gene_id != ti.gene_id:
            logger.warning("{ti.ac}: GeneID changed from {u_tx.gene_id} to {ti.gene_id}".format(u_tx=u_tx, ti=ti))

        # state: transcript now exists, either existing or freshly-created

        # 2. Upsert an ExonSet attached to the Transcript
        n, o = _upsert_exon_set_record(session, ti.ac, ti.ac, 1, self_aln_method, ti.exons_se_i)

        (no) = (n is not None, o is not None)
        if no == (True, False):
            n_new += 1
        elif no == (True, True):
            logger.warning("Transcript {ti.ac} exon structure changed".format(ti=ti))
            n_exons_changed += 1
        elif no == (False, True):
            logger.debug("Transcript {ti.ac} exon structure unchanged".format(ti=ti))
            n_unchanged += 1

        if i_ti % update_period == 0 or i_ti + 1 == n_rows:
            session.commit()
            logger.info("{i_ti}/{n_rows} {p:.1f}%; {n_new} new, {n_unchanged} unchanged, "
                        "{n_cds_changed} cds changed, {n_exons_changed} exons changed; commited".format(
                i_ti=i_ti, n_rows=n_rows,
                n_new=n_new, n_unchanged=n_unchanged, n_cds_changed=n_cds_changed, n_exons_changed=n_exons_changed,
                p=(i_ti + 1) / n_rows * 100))


def _create_translation_exceptions(transcript: str, transl_except_list: List[str]) -> List[Dict]:
    """
    Create TranslationException object data where start and end positions are 0-based, from transl_except data that is 1-based.
    For example, [(pos:333..335,aa:Sec), (pos:1017,aa:TERM)] should result in start and end positions [(332, 335), (1016, 1017)]
    """
    result = []

    for te in transl_except_list:
        # remove parens
        te = te.replace('(','').replace(')','')

        # extract positions
        pos_str, aa_str = te.split(',')
        pos_str = pos_str.removeprefix('pos:')
        if '..' in pos_str:
            start_position, _, end_position = pos_str.partition('..')
        else:
            start_position = end_position = pos_str

        # extract amino acid
        amino_acid = aa_str.removeprefix('aa:')

        result.append(
            {
                'tx_ac': transcript,
                'start_position': int(start_position) - 1,
                'end_position': int(end_position),
                'amino_acid': amino_acid,
            }
        )

    return result


def refresh_matviews(session, opts, cf):
    session.execute(text("set role {admin_role};".format(
        admin_role=cf.get("uta", "admin_role"))))
    session.execute(text("set search_path = " + usam.schema_name))

    # matviews must be updated in dependency order. Unfortunately,
    # it's difficult to determine this programmatically. The "right"
    # solution is a recursive CTE, but I was unable to find or write
    # one readily. This function should be consdered a placeholder for
    # the right way to update, which doesn't exist yet.

    # TODO: Determine mv refresh order programmatically.
    # sql = "select concat(schemaname,".",matviewname) as fqrn from pg_matviews where schemaname="{schema}"".format(
    #     schema=schema)
    # rows = list(session.execute(sql))
    # cmds = [ "refresh materialized view {fqrn}".format(fqrn=row["fqrn"]) for row in rows ]

    cmds = [
        # N.B. Order matters!
        "refresh materialized view exon_set_exons_fp_mv",
        "refresh materialized view tx_exon_set_summary_mv",
        "refresh materialized view tx_def_summary_mv",
        "refresh materialized view tx_exon_aln_mv",
    ]

    for cmd in cmds:
        logger.info(cmd)
        session.execute(text(cmd))
    session.commit()


def _get_mfdb(cf):
    from multifastadb import MultiFastaDB
    fa_dirs = cf.get("sequences", "fasta_directories").strip().splitlines()
    mfdb = MultiFastaDB(fa_dirs, use_meta_index=True)
    logger.info("Opened sequence directories: " + ",".join(fa_dirs))
    return mfdb

def _get_seqrepo(cf):
    sr_dir = cf.get("sequences", "seqrepo")
    sr = SeqRepo(root_dir=sr_dir, translate_ncbi_namespace=True)
    logger.info("Opened {sr}".format(sr=sr))
    return sr

_get_seqfetcher = _get_seqrepo


def _get_or_insert(
    session: Session,
    table: type[usam.Base],
    row: dict[str, Any],
    row_identifier: str | tuple[str, ...],
) -> tuple[usam.Base, bool]:
    """
    Returns a sqlalchemy model of the inserted or fetched row.

    `session` is a sqlalchemy session.
    `table` is the database table in which to insert `row`.
    `row` is the a list of key-value pairs to insert into the table.
    `row_identifier` is a map of key-value pairs which define a match between `row` and an existing row in the table.

    sqlalchemy.orm.exc.MultipleResultsFound may be raised if `row_identifier` does not uniquely identify a row.
    KeyError may be raised if `row_identifier` refers to columns not present as keys in `row`.
    sqlalchemy.exc.IntegrityError (raised from psycopg2.errors.ForeignKeyViolation) may be raised if a foreign key reference does not exist
    """
    row_filter = {ri: row[ri] for ri in row_identifier}
    try:
        row_instance = session.query(table).filter_by(**row_filter).one()
        created = False
    except NoResultFound:
        row_instance = table(**row)
        session.add(row_instance)
        created = True
    return row_instance, created


def _upsert_exon_set_record(session, tx_ac, alt_ac, strand, method, ess):

    """idempotent insert into exon_set and exon tables, archiving prior records if needed;
    returns tuple of (new_record, old_record) as follows:

    (new, None) -- no prior record; new was inserted
    (None, old) -- prior record and unchanged; nothing was inserted
    (new, old)  -- prior record existed and was changed

    """

    key = (tx_ac, alt_ac, method)

    existing = session.query(usam.ExonSet).filter(
        usam.ExonSet.tx_ac == tx_ac,
        usam.ExonSet.alt_ac == alt_ac,
        usam.ExonSet.alt_aln_method == method,
        )

    assert existing.count() <= 1, "Expected max 1 existing exon sets with key ({key})".format(key=key)

    if existing.count() == 1:
        es = existing[0]
        es_ess = es.exons_as_str(transcript_order=True)
        esh = hashlib.sha1(es_ess.encode("ascii")).hexdigest()[:8]
        alt_aln_method_with_hash = method + "/" + esh

        if es_ess == ess:
            # same as existing w/alt_aln_method=='transcript'
            return (None, es)

        # state: 1 exon set exists, and it differs from incoming

        # It's possible that we've seen this alternative before, so look again with hash
        existing = session.query(usam.ExonSet).filter(
            usam.ExonSet.tx_ac == tx_ac,
            usam.ExonSet.alt_ac == alt_ac,
            usam.ExonSet.alt_aln_method == alt_aln_method_with_hash,
            )
        if existing.count() == 1:
            logger.warning(
                "Exon set {tx_ac}/{alt_ac} with method {method} already exists with hash {esh}".format(
                    tx_ac=tx_ac,
                    alt_ac=alt_ac,
                    method=method,
                    esh=alt_aln_method_with_hash,
                )
            )
            return (None, existing[0])

        # update aln_method to add a unique exon set hash based on the *existing* exon set string
        logger.warning(
            "Exon set {tx_ac}/{alt_ac} with method {method} already exists, but with different exons; "
            "existing exon set: {es_ess}; new exon set: {ess}; updated alt_aln_method of exonset to "
            "{alt_aln_method_with_hash}".format(
                tx_ac=tx_ac,
                alt_ac=alt_ac,
                method=method,
                es_ess=es_ess,
                ess=ess,
                alt_aln_method_with_hash=alt_aln_method_with_hash,
            )
        )
        es.alt_aln_method = alt_aln_method_with_hash
        session.flush()
        old_es = es
    else:
        old_es = None

    es = usam.ExonSet(
        tx_ac=tx_ac,
        alt_ac=alt_ac,
        alt_aln_method=method,
        alt_strand=strand
        )
    session.add(es)

    exons = [tuple(map(int, se.split(","))) for se in ess.split(";")]
    exons.sort(reverse=int(strand) == MINUS_STRAND)
    for i_ex, ex in enumerate(exons):
        s, e = ex
        ex = usam.Exon(
            exon_set=es,
            start_i=s,
            end_i=e,
            ord=i_ex,
        )
        session.add(ex)

    return es, old_es


# <LICENSE>
# Copyright 2014 UTA Contributors (https://bitbucket.org/biocommons/uta)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
