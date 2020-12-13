from abc import ABC
from estnltk import Text
from datetime import datetime
from collections import Counter
from collections import deque
from configuration import Configuration
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from IPython.display import display
import html
import re


class CountConfiguration(Configuration, ABC):

    @property
    def name(self):
        return "count"

    def all_words_has_content(self, words):
        return all(set(word.partofspeech[0][0]) & {'A', 'C', 'U', 'V', 'S'} for word in words)

    def get_datasets(self, matrixes, filter_function=None):
        if filter_function is None:
            filter_function = self.all_words_has_content

        datasets = []
        for grouping, matrix_groupings in matrixes:
            print("Grouping: " + grouping + "\n\n")
            count_table = pd.DataFrame(columns=["group", "group_members", "in_a_row"] + sum(
                [["count_" + str(x), "repetitions_" + str(x)] for x in range(10)], []))
            for group_name, (group_members, matrix) in matrix_groupings:
                print("With group: " + group_name)
                print("With elements: " + str(group_members))
                for i in range(1, 5):
                    top_10 = []
                    for elem in matrix["counter_" + str(i)].most_common(10000):
                        words = [Text(x).tag_layer(["morph_analysis"]) for x in elem[0].split(" ")]
                        if filter_function(words):
                            top_10.append(elem)
                            if len(top_10) == 10:
                                break
                    add = dict()
                    add["group"] = group_name
                    add["group_members"] = str(group_members)
                    add["in_a_row"] = i
                    for x in range(10):
                        try:
                            add["count_" + str(x)] = [top_10[x][0]]
                            add["repetitions_" + str(x)] = [top_10[x][1]]
                        except Exception:
                            pass  # Empty field

                    try:
                        count_table = count_table.append(pd.DataFrame(add), sort=False)
                    except Exception as e:
                        pass  # Empty row
            datasets.append(count_table)

        return datasets

    def combine(self, first, second):
        combined = dict()
        people = first["people"]
        for i in range(1, 5):
            combined["counter_" + str(i)] = first["counter_" + str(i)] + second["counter_" + str(i)]

        for name in second["people"]:
            if not people.get(name):
                people[name] = second["people"][name]
            else:
                for item in second["people"][name]:
                    if not people[name].get(item):
                        people[name][item] = second["people"][name][item]
                    else:
                        people[name][item] += second["people"][name][item]

        combined["people"] = people
        return combined

    def get_empty(self):
        return {
            "last_timestamp": 0,
            "counter_1": Counter(),
            "counter_2": Counter(),
            "counter_3": Counter(),
            "counter_4": Counter(),
            "people": dict()
        }

    def apply(self, layer, message):
        timestamp = re.sub(r"(\.\d+)?[\+\-]\d+:\d+", "", message["timestamp"])
        new_time = datetime.strptime(''.join(timestamp), '%Y-%m-%dT%H:%M:%S').timestamp()
        if new_time > layer["last_timestamp"]:
            layer["last_timestamp"] = new_time

            parsed_text = Text(html.unescape(message["content"])).tag_layer(["morph_analysis"])
            parsed_user = html.unescape(message["author"]["name"])

            deques = [
                ("counter_1", deque(maxlen=1)),
                ("counter_2", deque(maxlen=2)),
                ("counter_3", deque(maxlen=3)),
                ("counter_4", deque(maxlen=4))
            ]

            for word in parsed_text.words:
                for key, q in deques:
                    q.extend([word.lemma])
                    if q.maxlen == len(q):
                        if not layer["people"].get(parsed_user):
                            layer["people"][parsed_user] = dict()
                        if not layer["people"][parsed_user].get(key):
                            layer["people"][parsed_user][key] = Counter()
                        layer["people"][parsed_user][key][" ".join(q)] += 1
                        layer[key][" ".join(q)] += 1

    def serialize(self, layer):
        for i in range(1, 5):
            layer["counter_" + str(i)] = dict(layer["counter_" + str(i)])
        for person in layer["people"].keys():
            for counter in layer["people"][person].keys():
                layer["people"][person][counter] = dict(layer["people"][person][counter])
        return layer

    def deserialize(self, layer):
        for i in range(1, 5):
            layer["counter_" + str(i)] = Counter(layer["counter_" + str(i)])
        for person in layer["people"].keys():
            for counter in layer["people"][person].keys():
                layer["people"][person][counter] = Counter(layer["people"][person][counter])
        return layer
