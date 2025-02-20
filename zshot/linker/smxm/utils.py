import os
import zipfile
from typing import List, Tuple

import torch
from transformers import BertTokenizerFast

from zshot.utils.data_models import Entity
from zshot.utils.data_models import Span
from zshot.linker.smxm.model import BertTaggerMultiClass
from zshot.utils import download_file

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SmxmInput(dict):
    def __init__(
            self,
            input_ids: torch.Tensor,
            attention_mask: torch.Tensor,
            token_type_ids: torch.Tensor,
            sep_index: torch.Tensor,
            seq_mask: torch.Tensor,
            split: torch.Tensor,
    ):
        config = {
            "input_ids": input_ids.to(device),
            "attention_mask": attention_mask.to(device),
            "token_type_ids": token_type_ids.to(device),
            "sep_index": sep_index.to(device),
            "seq_mask": seq_mask.to(device),
            "split": split.to(device),
        }
        super().__init__(**config)


def load_model(url: str, output_path: str, folder_name: str) -> BertTaggerMultiClass:
    filename = url.rsplit("/", 1)[1]
    model_zipfile_path = os.path.join(output_path, filename)
    model_folder_path = os.path.join(output_path, folder_name)

    if not os.path.isdir(model_folder_path):
        download_file(url, output_path)
        with zipfile.ZipFile(model_zipfile_path, "r") as model_zip:
            model_zip.extractall(output_path)
        os.remove(model_zipfile_path)

    model = BertTaggerMultiClass.from_pretrained(
        model_folder_path, output_hidden_states=True
    ).to(device)

    return model


def predictions_to_span_annotations(
        sentences: List[str],
        predictions: List[List[int]],
        probabilities: List[List[List[float]]],
        entities: List[str],
        tokenizer: BertTokenizerFast,
        max_sentence_tokens: int,
) -> List[List[Span]]:
    span_annotations = []

    for i, sentence in enumerate(sentences):
        sentence_span_annotations = []

        tokenization = tokenizer.encode_plus(
            sentence,
            return_token_type_ids=False,
            return_attention_mask=False,
            return_offsets_mapping=True,
        )

        num_tokens_full_sentence = len(tokenization["input_ids"]) - 2
        token_overflow = num_tokens_full_sentence - max_sentence_tokens
        truncation_offset = token_overflow * (token_overflow > 0)

        offset_mapping = tokenization["offset_mapping"]
        mapping_input_id_to_word = tokenization.encodings[0].word_ids
        words_offset_mappings = {}
        for j, w in enumerate(mapping_input_id_to_word):
            if w in words_offset_mappings:
                words_offset_mappings[w] = (
                    words_offset_mappings[w][0],
                    offset_mapping[j][1],
                )
            elif w is not None:
                words_offset_mappings[w] = offset_mapping[j]

        for j, input_id in enumerate(mapping_input_id_to_word[truncation_offset:-1]):
            pred = predictions[i][j]
            if (
                    entities[pred] != "NEG"
            ) and (
                    input_id is not None
            ) and (
                    (j == 0) or (input_id != mapping_input_id_to_word[j - 1])
            ) and (
                    (words_offset_mappings[input_id][1] - words_offset_mappings[input_id][0]) > 1
            ):
                if (
                        sentence_span_annotations and (sentence_span_annotations[-1].label == entities[pred])
                ) and (
                        sentence_span_annotations[-1].end == words_offset_mappings[input_id][0] - 1
                ):
                    sentence_span_annotations[-1].end = words_offset_mappings[input_id][1]
                    sentence_span_annotations[-1].score = max(sentence_span_annotations[-1].score,
                                                              probabilities[i][j][pred])
                else:
                    sentence_span_annotations.append(
                        Span(words_offset_mappings[input_id][0], words_offset_mappings[input_id][1],
                             entities[pred], probabilities[i][j][pred])
                    )
        span_annotations.append(sentence_span_annotations)

    return span_annotations


def get_entities_names_descriptions(
        entities: List[Entity],
) -> Tuple[List[str], List[str]]:
    if "NEG" in [e.name for e in entities]:
        neg_index = [e.name for e in entities].index("NEG")
        entities.insert(0, entities.pop(neg_index))
    else:
        neg_ent = Entity(
            name="NEG",
            description="Coal, water, oil, etc. are normally used for traditional electricity generation. "
                        "However using liquefied natural gas as fuel for joint circulatory electircity generation has advantages. "
                        "The chief financial officer is the only one there taking the fall. It has a very talented team, eh. "
                        "What will happen to the wildlife? I just tell them, you've got to change. They're here to stay. "
                        "They have no insurance on their cars. What else would you like? Whether holding an international cultural event "
                        "or setting the city's cultural policies, she always asks for the participation or input of other cities and counties.",
        )
        entities.insert(0, neg_ent)

    entity_labels = [e.name for e in entities]
    entity_descriptions = [e.description for e in entities]

    return entity_labels, entity_descriptions
