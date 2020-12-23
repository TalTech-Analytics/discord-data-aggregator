from abc import ABC
from estnltk import Text
from collections import Counter
from collections import deque
from configuration import Configuration
import pandas as pd
import html

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class CountConfiguration(Configuration, ABC):

    @property
    def name(self):
        return "count"

    @staticmethod
    def all_words_have_context(words):
        return all(
            len(word["analysis"][0]['lemma']) >= 4 and set(word["analysis"][0]['partofspeech']) & {'A', 'S', 'Y'} for
            word in words)

    @staticmethod
    def all_words_has_content(words):
        return all(
            len(word["analysis"][0]['lemma']) >= 3 and set(word["analysis"][0]['partofspeech']) & {'A', 'C', 'U', 'V',
                                                                                                   'S', 'Y'} for word in
            words)

    def get_datasets(self, matrixes, filter_function=None):
        if filter_function is None:
            filter_function = self.all_words_has_content

        datasets = []
        for grouping, matrix_groupings in matrixes:
            print("Grouping: " + grouping + "\n\n")
            headers = ["group", "group_members", "total_words", "in_a_row"]
            headers += sum([["count_" + str(x), "repetitions_" + str(x)] for x in range(10)], [])
            headers += sum(
                [["valence_only_" + x, "valence_mostly_" + x] for x in ["negative", "neutral", "mixed", "positive"]],
                [])
            count_table = pd.DataFrame(columns=headers)
            for group_name, (group_members, matrix) in matrix_groupings:
                print("With group: " + group_name)
                print("With elements: " + str(group_members))
                for i in range(1, 5):
                    top_10 = self.get_top_10_words(filter_function, i, matrix)

                    for j, (item, repetitions) in enumerate(top_10):
                        add = dict()
                        add["rank"] = j
                        add["item"] = item
                        add["repetitions"] = repetitions
                        add["group"] = group_name
                        add["group_members"] = ",".join(group_members)
                        add["total_words"] = matrix["total_words"]
                        add["in_a_row"] = i

                        for status in ["only", "mostly"]:
                            for emotion in ["negative", "neutral", "mixed", "positive"]:
                                key = "valence_" + status + "_" + emotion
                                add[key] = matrix[key]

                        try:
                            count_table = count_table.append(pd.DataFrame(add, index=[0]), ignore_index=True, sort=False)
                        except Exception as e:
                            pass  # Empty row
            datasets.append(count_table.sort_values(by='group'))

        return datasets

    @staticmethod
    def get_top_10_words(filter_function, i, matrix):
        top_10 = []
        print("Items in: counter_" + str(i) + ": " + str(len(matrix["counter_" + str(i)])))
        for elem in matrix["counter_" + str(i)].most_common(10000):
            words = Text(elem[0]).tag("analysis").words
            if filter_function(words):
                top_10.append(elem)
                if len(top_10) == 10:
                    break
        return top_10

    def combine(self, first, second):
        combined = dict()

        for i in range(1, 5):
            combined["counter_" + str(i)] = first["counter_" + str(i)] + second["counter_" + str(i)]
        combined["total_words"] = first["total_words"] + second["total_words"]

        for status in ["only", "mostly"]:
            for emotion in ["negative", "neutral", "mixed", "positive"]:
                key = "valence_" + status + "_" + emotion
                combined[key] = first[key] + second[key]

        return combined

    def get_empty(self):
        return {
            "valence_only_negative": 0,
            "valence_only_neutral": 0,
            "valence_only_positive": 0,
            "valence_only_mixed": 0,
            "valence_mostly_negative": 0,
            "valence_mostly_neutral": 0,
            "valence_mostly_positive": 0,
            "valence_mostly_mixed": 0,
            "total_words": 0,
            "counter_1": Counter(),
            "counter_2": Counter(),
            "counter_3": Counter(),
            "counter_4": Counter()
        }

    def apply(self, layer, message):
        new_words = 0
        parsed_text = Text(html.unescape(message["content"])).tag("analysis")

        deques = [
            ("counter_1", deque(maxlen=1)),
            ("counter_2", deque(maxlen=2)),
            ("counter_3", deque(maxlen=3)),
            ("counter_4", deque(maxlen=4))
        ]

        for word in parsed_text.words:
            new_words += 1
            for key, q in deques:
                lemma = word["analysis"][0]['lemma'].lower()
                q.extend([lemma])
                if q.maxlen == len(q):
                    layer[key][" ".join(q)] += 1

        layer["total_words"] += new_words
        emotion = message["valence"].replace(" ", "_").lower()
        if emotion:
            layer["valence_" + emotion] += new_words

    def serialize(self, layer):
        for i in range(1, 5):
            layer["counter_" + str(i)] = dict(layer["counter_" + str(i)])
        return layer

    def deserialize(self, layer):
        for i in range(1, 5):
            layer["counter_" + str(i)] = Counter(layer["counter_" + str(i)])
        return layer
