import os
import json
from configuration import Configuration


class CachedRunner:
    def __init__(self, config):
        """directory: all files in given folder and subfolder will be used."""
        self.config = config
        self.data_dir = "/analyzer/input"
        self.data_out = "/analyzer/tmp"

    def get_datasets(self, fresh=False, filter_function=None):
        self.invoke(clean=fresh)
        matrixes = self.get_reduced_matrixes()
        return self.config.get_datasets(matrixes, filter_function=filter_function)

    def get_reduced_matrixes(self):
        reduced_matrixes = []
        for name, matrix in [
            # TODO: all together
            ("Year", self.get_year_matrix()),
            ("Year category", self.get_year_category_matrix()),
            ("Flat", self.get_flattened_matrix()),
            ("Category", self.get_category_matrix())
        ]:
            reduced_matrix = []
            print("Reducing: " + name)
            for grouping, group_values in matrix.items():
                reduced_matrix_row = [[], self.config.get_empty()]
                print("\n\nFound group: " + grouping, end=" with elements: ")
                for group_name, group_value in group_values:
                    print(group_name, end=" ")
                    reduced_matrix_row[0].append(group_name)
                    reduced_matrix_row[1] = self.config.combine(reduced_matrix_row[1], group_value)
                print("\n")
                reduced_matrix.append((grouping, reduced_matrix_row))
            reduced_matrixes.append((name, reduced_matrix))
        return reduced_matrixes

    ### MATRIXES
    # Matrixes must have the type of Map<grouping, List<Tuple<name, Configuration.empty>>>

    def get_year_matrix(self):
        matrix = dict()
        for guild in self.get_guilds():
            row = []
            guild_name = guild["name"]
            for channel in self.get_channels_in_guild(guild):
                channel_name = channel["name"]
                channel = self.get_channel(guild, channel)
                row.append((channel_name, channel))
            matrix[guild_name] = row
        return matrix

    def get_flattened_matrix(self):
        matrix = dict()
        for guild in self.get_guilds():
            guild_name = guild["name"]
            for channel in self.get_channels_in_guild(guild):
                channel_name = channel["name"]
                channel = self.get_channel(guild, channel)
                matrix[channel_name] = [(channel_name, channel)]
        return matrix

    def get_year_category_matrix(self):
        matrix = dict()
        for guild in self.get_guilds():
            guild_name = guild["name"]
            for channel in self.get_channels_in_guild(guild):
                channel_name = channel["name"]
                grouping = (channel_name.split("/")[0]).strip()
                grouping = guild_name + " " + grouping
                channel = self.get_channel(guild, channel)
                if not matrix.get(grouping):
                    matrix[grouping] = []
                matrix[grouping].append((channel_name, channel))
        return matrix

    def get_category_matrix(self):
        matrix = dict()
        for guild in self.get_guilds():
            guild_name = guild["name"]
            for channel in self.get_channels_in_guild(guild):
                channel_name = channel["name"]
                grouping = (channel_name.split("/")[0]).strip()
                channel = self.get_channel(guild, channel)
                if not matrix.get(grouping):
                    matrix[grouping] = []
                matrix[grouping].append((channel_name, channel))
        return matrix

    ### FILE GETTERS

    def get_guilds(self):
        try:
            guilds_file = open(os.path.join(self.data_out, self.config.name + "_cache_guilds.json"), "r")
            guilds = json.load(guilds_file)
            guilds_file.close()
            return guilds["guilds"]
        except Exception as e:
            return []

    def get_channels_in_guild(self, guild):
        try:
            channels_file = open(
                os.path.join(self.data_out, str(guild["id"]), self.config.name + "_cache_channels.json"), "r")
            channels = json.load(channels_file)
            channels_file.close()
            return channels["channels"]
        except Exception as e:
            return []

    def get_channel(self, guild, channel):
        try:
            channel_path = os.path.join(self.data_out, str(guild["id"]), str(channel["id"]),
                                        self.config.name + "_cache_channel.json")
            channel_file = open(channel_path, "r")
            channel = self.config.deserialize(json.load(channel_file))
            channel_file.close()
            return channel
        except Exception as e:
            return self.config.get_empty()

    ### UPDATE CACHE

    def invoke(self, directory="/analyzer/input", clean=False):
        """
        Update cache or create one with given and return the results.

        preconditions:
        term count of apply must be 2: (given_structure, discord_message)
        term count of serializer must be 1
        term count of deserializer must be 1

        next functions must make inplace mutations:
        serializer, deserializer, function_to_apply

        postcondition:
        a list of filled versions of default_structures are returned
        """

        for f in os.listdir(directory):
            cache_file_prefix = self.config.name + "_cache_"
            cache_location = os.path.join(directory.replace(self.data_dir, self.data_out), cache_file_prefix + f)
            cur_path = os.path.join(directory, f)

            if not os.path.isfile(cur_path):
                self.invoke(cur_path)

            else:
                print("processing: " + cur_path + " cache: " + cache_location)
                os.makedirs(os.path.dirname(cache_location), exist_ok=True)

                # Create empty cache if needed
                if not os.path.isfile(cache_location) or clean:
                    cache = open(cache_location, "w")
                    json.dump(self.config.serialize(self.config.get_empty()), cache)
                    cache.close()

                cur_layer = self.config.get_empty()
                try:
                    # Read current version
                    cache = open(cache_location, "r")
                    cur_layer = self.config.deserialize(json.load(cache))
                    cache.close()
                except Exception:
                    # Delete and create a new one
                    os.remove(cache_location)
                    cache = open(cache_location, "w")
                    json.dump(self.config.serialize(cur_layer), cache)
                    cache.close()

                # Update cache
                discord_data = open(cur_path, "r")
                raw_json = json.load(discord_data)

                try:
                    for message in raw_json["messages"]:
                        self.config.apply(cur_layer, message)

                    discord_data.close()

                    # Save updated version
                    cache = open(cache_location, "w")
                    json.dump(self.config.serialize(cur_layer), cache)
                    cache.close()
                except Exception:
                    # Save initial version
                    cache = open(cache_location, "w")
                    json.dump(raw_json, cache)
                    cache.close()
