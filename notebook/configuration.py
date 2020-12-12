from abc import ABCMeta, abstractmethod


class Configuration:
    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def name(self):
        return "generic"

    @abstractmethod
    def get_datasets(self, matrixes, filter_function=None):
        return None

    @abstractmethod
    def combine(self, first, second):
        return first

    @abstractmethod
    def get_empty(self):
        return {
        }

    @abstractmethod
    def apply(self, layer, message):
        return {}

    @abstractmethod
    def serialize(self, layer):
        return layer

    @abstractmethod
    def deserialize(self, layer):
        return layer
