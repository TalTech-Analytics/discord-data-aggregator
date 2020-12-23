from concat_configuration import ConcatConfiguration
from count_configuration import CountConfiguration
from textrank_analyzer import TextRankAnalyzer
from quantitative_metrics import QuantitativeMetrics
from cached_runner import CachedRunner

data_out = "/analyzer/output"


def dump_count_tables():
    count_configuration = CountConfiguration()
    count_runner = CachedRunner(count_configuration)
    count_matrixes = count_runner.get_datasets(fresh=False, filter_function=count_configuration.all_words_have_context)
    count_dfs = [
        ("count_all.json", count_matrixes[0]),
        ("count_group_year.json", count_matrixes[1]),
        ("count_year_channels.json", count_matrixes[2]),
        ("count_flat.json", count_matrixes[3]),
        ("count_group_category.json", count_matrixes[4])
    ]
    for name, df in count_dfs:
        with open(data_out + "/" + name, 'w') as f:
            f.write(df.to_json(orient='records', lines=True))


def dump_concat_tables():
    concat_configuration = ConcatConfiguration()
    concat_runner = CachedRunner(concat_configuration)
    concat_matrixes = concat_runner.get_datasets(fresh=False)
    concat_dfs = [
        ("concat_all.json", concat_matrixes[0]),
        ("concat_year.json", concat_matrixes[1]),
        ("concat_year_channels.json", concat_matrixes[2]),
        ("concat_flat.json", concat_matrixes[3]),
        ("concat_group_category.json", concat_matrixes[4])
    ]

    for name, df in concat_dfs:
        with open(data_out + "/" + name, 'w') as f:
            f.write(df.to_json(orient='records', lines=True))

    dump_quantitative_metric_tables(concat_dfs)
    dump_textrank_tables(concat_dfs)


def dump_textrank_tables(concat_dfs):
    for name, df in concat_dfs:
        textrank_df = TextRankAnalyzer().analyze(df)
        with open(data_out + "/" + name.replace("concat", "textrank"), 'w') as f:
            f.write(textrank_df.to_json(orient='records', lines=True))


def dump_quantitative_metric_tables(concat_dfs):
    for name, df in concat_dfs:
        quantitative_metrics_df = QuantitativeMetrics().analyze(df)
        with open(data_out + "/" + name.replace("concat", "quantitative_metrics"), 'w') as f:
            f.write(quantitative_metrics_df.to_json(orient='records', lines=True))


if __name__ == '__main__':
    dump_concat_tables()
    dump_count_tables()
