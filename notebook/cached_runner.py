import json
import os
import shutil


class CachedRunner:
    def __init__(self, config):
        """directory: all files in given folder and subfolder will be used."""
        self.config = config
        self.data_dir = "/analyzer/input"
        self.data_tmp = "/analyzer/tmp"

    def get_datasets(self, fresh=False, filter_function=None):
        global cached_runner_matrixes

        if not fresh:
            print("Using cache in RAM")
            try:
                cached_runner_matrixes
            except Exception:
                cached_runner_matrixes = dict()

            try:
                cached_runner_matrixes[self.config.name]
            except Exception:
                self.invoke(clean=fresh)
                cached_runner_matrixes[self.config.name] = self.get_reduced_matrixes()
        else:
            print("Recreating cache in RAM from permanent storage cache")
            shutil.rmtree(self.data_tmp)
            os.mkdir(self.data_tmp)
            cached_runner_matrixes = dict()
            self.invoke(clean=fresh)
            cached_runner_matrixes[self.config.name] = self.get_reduced_matrixes()

        return self.config.get_datasets(cached_runner_matrixes[self.config.name], filter_function=filter_function)

    def get_reduced_matrixes(self):
        reduced_matrixes = []
        for name, matrix in [
            ("All", self.get_combined_matrix()),
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
                    print(group_name, end="   ")
                    reduced_matrix_row[0].append(group_name)
                    reduced_matrix_row[1] = self.config.combine(reduced_matrix_row[1], group_value)
                print("\n")
                reduced_matrix.append((grouping, reduced_matrix_row))
            reduced_matrixes.append((name, reduced_matrix))
        return reduced_matrixes

    # MATRIXES
    # Matrixes must have the type of Map<grouping, List<Tuple<name, Configuration.empty>>>

    def get_combined_matrix(self):
        matrix = dict()
        row = []
        for guild in self.get_guilds():
            for channel in self.get_channels_in_guild(guild):
                channel_name = channel["name"]
                channel = self.get_channel(guild, channel)
                row.append((channel_name, channel))
        matrix["all"] = row
        return matrix

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
                grouping = (channel_name.split("/")[0]).strip().lower()
                grouping = guild_name + " " + grouping
                channel = self.get_channel(guild, channel)
                if not matrix.get(grouping):
                    matrix[grouping] = []
                matrix[grouping].append((channel_name, channel))
        return matrix

    def get_category_matrix(self):
        matrix = dict()
        for guild in self.get_guilds():
            for channel in self.get_channels_in_guild(guild):
                channel_name = channel["name"]
                grouping = (channel_name.split("/")[0]).strip().lower()
                channel = self.get_channel(guild, channel)
                if not matrix.get(grouping):
                    matrix[grouping] = []
                matrix[grouping].append((channel_name, channel))
        return matrix

    # FILE GETTERS

    def get_guilds(self):
        try:
            with open(os.path.join(self.data_dir, "guilds.json"), "r") as guilds_file:
                guilds = json.load(guilds_file)
                return guilds["guilds"]
        except Exception as e:
            print("Failed fetching guilds:" + str(e))
            return []

    def get_channels_in_guild(self, guild):
        try:
            with open(os.path.join(self.data_dir, str(guild["id"]), "channels.json"), "r") as channels_file:
                channels = json.load(channels_file)
                return channels["channels"]
        except Exception as e:
            print("Failed fetching channels:" + str(e))
            return []

    def get_channel(self, guild, channel):
        try:
            channel_path = os.path.join(self.data_tmp, str(guild["id"]), str(channel["id"]),
                                        self.config.name + "_cache_channel.json")
            with open(channel_path, "r") as channel_file:
                channel = self.config.deserialize(json.load(channel_file))
                return channel
        except Exception as e:
            print("Failed fetching channel:" + str(e))
            return self.config.get_empty()

    # UPDATE CACHE

    def invoke(self, clean=False):
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
        for guild in self.get_guilds():
            for channel in self.get_channels_in_guild(guild):
                input_location = os.path.join(self.data_dir, str(guild["id"]), str(channel["id"]), "channel.json")
                cache_location = os.path.join(self.data_tmp, str(guild["id"]), str(channel["id"]),
                                              self.config.name + "_cache_channel.json")
                print("processing: " + input_location + " cache: " + cache_location)
                os.makedirs(os.path.dirname(cache_location), exist_ok=True)

                if not os.path.isfile(input_location):
                    print("skipping")
                    continue

                # Create empty cache if needed
                if not os.path.isfile(cache_location) or clean:
                    self.create_empty(cache_location)

                cur_layer = self.get_current(cache_location)

                self.update_cache(cache_location, cur_layer, input_location)

    def update_cache(self, cache_location, cur_layer, input_location):
        with open(input_location, "r") as discord_data:
            raw_json = json.load(discord_data)

            try:
                self.update_messages(cache_location, cur_layer, discord_data, raw_json)
            except Exception as error:
                print("Failed updating: " + str(error))
                # Save initial version
                with open(cache_location, "w") as cache:
                    json.dump(raw_json, cache)

    def update_messages(self, cache_location, cur_layer, discord_data, raw_json):
        for message in raw_json["messages"]:
            try:
                self.config.apply(cur_layer, message)
            except Exception as error:
                print("error invoking: " + str(error))
        discord_data.close()

        # Save updated version
        with open(cache_location, "w") as cache:
            json.dump(self.config.serialize(cur_layer), cache)

    def get_current(self, cache_location):
        cur_layer = self.config.get_empty()
        try:
            # Read current version
            with open(cache_location, "r") as cache:
                cur_layer = self.config.deserialize(json.load(cache))

        except Exception as error:
            print("Failed reading: " + str(error))
            # Delete and create a new one
            os.remove(cache_location)
            with open(cache_location, "w") as cache:
                json.dump(self.config.serialize(self.config.get_empty()), cache)
        return cur_layer

    def create_empty(self, cache_location):
        print("emptying cache in: " + cache_location)
        if os.path.exists(cache_location):
            os.remove(cache_location)
        with open(cache_location, "w") as cache:
            json.dump(self.config.serialize(self.config.get_empty()), cache)
