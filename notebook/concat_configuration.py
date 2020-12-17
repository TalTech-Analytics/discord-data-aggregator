from abc import ABC
from estnltk import Text
from datetime import datetime
from configuration import Configuration
import pandas as pd
import html
import re

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class ConcatConfiguration(Configuration, ABC):

    @property
    def name(self):
        return "concat"

    def get_datasets(self, matrixes, filter_function=None):
        datasets = []
        for grouping, matrix_groupings in matrixes:
            print("Grouping: " + grouping + "\n\n")
            count_table = pd.DataFrame(columns=["group", "group_members", "text"])
            for group_name, (group_members, matrix) in matrix_groupings:
                print("With group: " + group_name)
                print("With elements: " + str(group_members))
                add = dict()
                add["group"] = group_name
                add["group_members"] = str(group_members)
                add["text"] = " ".join(matrix["text"])
                print("Data length: " + str(len(add["text"])))
                count_table = count_table.append(pd.DataFrame(add, index=[0]), ignore_index=True, sort=False)
            datasets.append(count_table.sort_values(by='group'))
        return datasets

    def combine(self, first, second):
        combined = dict()
        combined["text"] = first["text"] + second["text"]
        return combined

    def get_empty(self):
        return {
            "last_timestamp": 0,
            "text": []
        }

    def apply(self, layer, message):
        timestamp = re.sub(r"(\.\d+)?[+\-]\d+:\d+", "", message["timestamp"])
        new_time = datetime.strptime(''.join(timestamp), '%Y-%m-%dT%H:%M:%S').timestamp()
        if new_time > layer["last_timestamp"]:
            layer["last_timestamp"] = new_time
            parsed_text = html.unescape(message["content"])
            if re.match(r"^.+\w$", parsed_text):
                parsed_text += "."
            layer["text"].append(parsed_text)

    def serialize(self, layer):
        layer["text"] = " ".join(layer["text"])
        return layer

    def deserialize(self, layer):
        layer["text"] = [layer["text"]]
        return layer
