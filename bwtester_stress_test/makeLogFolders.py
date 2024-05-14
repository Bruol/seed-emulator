
import os

BASE_LOG_DIR = "/home/ubuntu/bt/seed-emulator/bwtester_stress_test/logs"


def createLogFolders():
    with open("/home/ubuntu/bt/seed-emulator/bwtester_stress_test/asns","r") as f:
        asns_str = f.read()

    ases = asns_str.split(",")

    # create log folders
    os.mkdir(BASE_LOG_DIR)

    for asn in ases:
        os.mkdir(BASE_LOG_DIR + "/" + str(asn))


if __name__ == "__main__":
    createLogFolders()