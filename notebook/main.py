from count_configuration import CountConfiguration
from cached_runner import CachedRunner

configuration = CountConfiguration()
count_runner = CachedRunner(configuration)
reduced_matrixes = count_runner.get_datasets()
