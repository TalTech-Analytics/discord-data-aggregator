import pandas as pd
from estnltk import Text
from summa.summarizer import summarize
from summa.keywords import keywords


class TextRankAnalyzer:

    @staticmethod
    def word_has_context(word):
        return len(word["analysis"][0]['lemma']) >= 4 and set(word["analysis"][0]['partofspeech']) & {'A', 'S', 'Y'}

    def analyze(self, df_with_text):
        headers = ["group", "group_members", "summary"]
        headers += ["keyword_" + str(i) for i in range(20)]
        textrank_table = pd.DataFrame(columns=headers)

        for index, row in df_with_text.iterrows():
            if len(row["text"]) < 50000:
                add = dict()
                add["group"] = row["group"]
                add["group_members"] = row["group_members"]
                self.add_summary(add, row)
                self.add_keywords(add, row)
                textrank_table = textrank_table.append(pd.DataFrame(add, index=[0]), ignore_index=True, sort=False)

        return textrank_table

    @staticmethod
    def add_summary(add, row):
        try:
            add["summary"] = summarize(row["text"], words=50, language='finnish')
        except Exception:
            add["summary"] = ""

    def add_keywords(self, add, row):
        words = Text(row["text"]).tag("analysis").words
        context_text = " ".join([word["analysis"][0]['lemma'] for word in words if self.word_has_context(word)])

        try:
            extracted_keywords = keywords(context_text, words=20, language='finnish', split=True)
        except Exception:
            extracted_keywords = ["" for _ in range(20)]

        for i in range(20):
            try:
                add["keyword_" + str(i)] = extracted_keywords[i]
            except Exception:
                add["keyword_" + str(i)] = ""
