#!/usr/bin/env python3

import os
import re
import subprocess
import sys

from ansible_vault import Vault

# Define the input and output file paths
input_file = sys.argv[1]
output_file = sys.argv[2]
# Get home directory
home = os.path.expanduser("~")
# Define the vault password variable name in gopass
VPVAR = ".vault_pass-var"


def strip_quotes_and_spaces(astring):
    rstring = astring.replace('"', "")
    return rstring.strip()


# Function to decrypt a vault string
def decrypt_vault_string(encrypted_string):
    vault_password = subprocess.check_output(["gopass", "cat", VPVAR]).decode("utf-8").strip()
    vault = Vault(vault_password)
    decrypted_string = vault.load(encrypted_string.strip())
    return decrypted_string


# Read the input file
with open(input_file, "r") as infile:
    lines = infile.readlines()

# Prepare to write to the output file
with open(output_file, "w") as outfile:
    encrypted_block = []
    inside_vault_block = False

    for line in lines:
        if re.match(r"^\s*\$ANSIBLE_VAULT;", line):
            inside_vault_block = True
            encrypted_block.append(f"{strip_quotes_and_spaces(line)}\n")
        elif inside_vault_block:
            if line.strip() == "":
                inside_vault_block = False
                encrypted_string = "".join(encrypted_block)
                print(f"Encrypted string: {encrypted_string}")
                decrypted_string = decrypt_vault_string(encrypted_string)
                outfile.write(decrypted_string + "\n")
                encrypted_block = []
            else:
                encrypted_block.append(strip_quotes_and_spaces(line))
        else:
            outfile.write(line)

    # Handle any remaining encrypted block
    if encrypted_block:
        encrypted_string = "".join(encrypted_block)
        print(f"Encrypted string: {encrypted_string}")
        decrypted_string = decrypt_vault_string(encrypted_string)
        outfile.write(decrypted_string + "\n")

print(f"Decryption complete. Decrypted content written to {output_file}")
