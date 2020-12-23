import pandas as pd
from estnltk import Text


class QuantitativeMetrics:

    # https://en.wikipedia.org/wiki/Lexical_density
    @staticmethod
    def get_lexical_density(words):
        content_words = 0
        for word in words:
            if set(word["analysis"][0]['partofspeech']) & {'A', 'C', 'U', 'V', 'S'}:
                content_words += 1
        return round(100 * content_words / max(len(words), 1), 2)

    # https://rdrr.io/github/trinker/formality/man/formality.html
    @staticmethod
    def get_formality(words):
        f = 1
        c = 1
        for word in words:
            if set(word["analysis"][0]['partofspeech']) & {'S', 'A', 'C', 'U', 'K'}:
                f += 1
            elif set(word["analysis"][0]['partofspeech']) & {'P', 'V', 'D', 'I'}:
                c += 1
        return round(50 * ((f - c) / (f + c) + 1), 2)

    @staticmethod
    def count_syllables(word: str) -> int:
        syllable_count = 0
        vowels = "aeiouõäöü"
        if not word:
            return 0
        if word[0] in vowels:
            syllable_count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                syllable_count += 1
        if syllable_count == 0:
            syllable_count += 1
        return syllable_count

    # https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests
    @staticmethod
    def get_fres(words, nr_of_sentences):
        syllables = sum([QuantitativeMetrics.count_syllables(x["analysis"][0]['root']) for x in words])
        a = 206.835 - 1.015 * max(len(words), 1) / max(nr_of_sentences, 1)
        b = 84.6 * syllables / max(len(words), 1)
        return round(a - b, 2)

    # https://en.wikipedia.org/wiki/Gunning_fog_index
    @staticmethod
    def get_gunning_fog(words, nr_of_sentences):
        difficult_words = sum(
            [max([QuantitativeMetrics.count_syllables(word) for word in x["analysis"][0]["root_tokens"]]) >= 3 for x in
             words])
        return round(0.4 * max(len(words), 1) / max(nr_of_sentences, 1) + 100 * difficult_words / max(len(words), 1), 2)

    def analyze(self, df):
        headers = ["group", "fres", "gunning_fog", "lexical_density", "formality"]
        quantitative_table = pd.DataFrame(columns=headers)

        for index, row in df.iterrows():
            text = Text(row["text"]).tag("analysis")
            add = dict()
            add["group"] = row["group"]
            add["fres"] = self.get_fres(text.words, len(text.sentences))
            add["gunning_fog"] = self.get_gunning_fog(text.words, len(text.sentences))
            add["lexical_density"] = self.get_lexical_density(text.words)
            add["formality"] = self.get_formality(text.words)
            quantitative_table = quantitative_table.append(pd.DataFrame(add, index=[0]), ignore_index=True, sort=False)

        return quantitative_table.sort_values(by='group')
