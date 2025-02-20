import pkgutil

import spacy

from zshot.mentions_extractor import MentionsExtractorFlair
from zshot.mentions_extractor.mentions_extractor_flair import ExtractorType
from zshot.tests.config import EX_DOCS
from zshot import PipelineConfig


def test_flair_ner_mentions_extractor():
    if not pkgutil.find_loader("flair"):
        return
    nlp = spacy.blank("en")
    config_zshot = PipelineConfig(mentions_extractor=MentionsExtractorFlair(ExtractorType.NER))
    nlp.add_pipe("zshot", config=config_zshot, last=True)
    assert "zshot" in nlp.pipe_names
    doc = nlp(EX_DOCS[1])
    assert doc.ents == ()
    assert len(doc._.mentions) > 0


def test_custom_flair_mentions_extractor():
    nlp = spacy.blank("en")
    config_zshot = PipelineConfig(mentions_extractor=MentionsExtractorFlair(ExtractorType.NER))
    nlp.add_pipe("zshot", config=config_zshot, last=True)
    assert "zshot" in nlp.pipe_names
    doc = nlp(EX_DOCS[1])
    assert doc.ents == ()
    assert len(doc._.mentions) > 0


def test_flair_pos_mentions_extractor():
    if not pkgutil.find_loader("flair"):
        return
    nlp = spacy.blank("en")

    config_zshot = PipelineConfig(mentions_extractor=MentionsExtractorFlair(ExtractorType.POS))
    nlp.add_pipe("zshot", config=config_zshot, last=True)
    assert "zshot" in nlp.pipe_names
    doc = nlp(EX_DOCS[1])
    assert doc.ents == ()
    assert len(doc._.mentions) > 0


def test_flair_ner_mentions_extractor_pipeline():
    if not pkgutil.find_loader("flair"):
        return
    nlp = spacy.blank("en")
    config_zshot = PipelineConfig(mentions_extractor=MentionsExtractorFlair(ExtractorType.NER))
    nlp.add_pipe("zshot", config=config_zshot, last=True)
    assert "zshot" in nlp.pipe_names
    docs = [doc for doc in nlp.pipe(EX_DOCS)]
    assert all(doc.ents == () for doc in docs)
    assert all(len(doc._.mentions) > 0 for doc in docs)


def test_flair_pos_mentions_extractor_pipeline():
    if not pkgutil.find_loader("flair"):
        return
    nlp = spacy.blank("en")
    config_zshot = PipelineConfig(mentions_extractor=MentionsExtractorFlair(ExtractorType.POS))
    nlp.add_pipe("zshot", config=config_zshot, last=True)
    assert "zshot" in nlp.pipe_names
    docs = [doc for doc in nlp.pipe(EX_DOCS)]
    assert all(doc.ents == () for doc in docs)
    assert all(len(doc._.mentions) > 0 for doc in docs)
