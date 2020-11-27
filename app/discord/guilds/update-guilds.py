import subprocess
import os
import re
import json

log_pattern = r"^.*\s(\d*) \| (.*)$"


def update_guilds():
    collect_data()
    process_data()
    cleanup()


def cleanup():
    os.remove("../tmp/guilds.log")
    subprocess.call("docker-compose -f docker-compose-discord-guilds.yml down --remove-orphans", shell=True)


def process_data():
    try:
        update_guilds_json()
    except Exception:
        os.remove("../data/guilds.json")


def collect_data():
    with open("../tmp/guilds.log", "a") as output:
        subprocess.call("docker-compose -f docker-compose-discord-guilds.yml up", shell=True, stdout=output)


def update_guilds_json():
    with open("../tmp/guilds.log", "r") as output:
        content = "\n".join(output.readlines())

        matches = re.finditer(log_pattern, content, re.MULTILINE)
        guilds_list = []
        guilds_list_duplicates = set()
        guilds_json = {"guilds": guilds_list}

        guilds_json, guilds_list = fetch_existing(guilds_json, guilds_list, guilds_list_duplicates)
        update_existing(guilds_list, guilds_list_duplicates, matches)
        dump_existing(guilds_json)


def dump_existing(guilds_json):
    with open("../data/guilds.json", "w") as guilds_output:
        json.dump(guilds_json, guilds_output)


def update_existing(guilds_list, guilds_list_duplicates, matches):
    for matchNum, match in enumerate(matches, start=1):
        print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
                                                                            end=match.end(), match=match.group()))
        if match.group(2) not in guilds_list_duplicates:
            folder_path = "../data/" + match.group(1)
            try:
                os.mkdir(folder_path)
                print("Making a folder as it didn't exist:", folder_path)
            except Exception:
                pass
            guilds_list.append({"name": match.group(2), "id": int(match.group(1))})


def fetch_existing(guilds_json, guilds_list, guilds_list_duplicates):
    if os.path.isfile("../data/guilds.json"):
        with open("../data/guilds.json", "r") as guilds_existing:
            guilds_json = json.load(guilds_existing)
            guilds_list = guilds_json["guilds"]
            for guild in guilds_list:
                guilds_list_duplicates.add(guild["name"])
    return guilds_json, guilds_list


if __name__ == '__main__':
    update_guilds()
