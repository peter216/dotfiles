#!/usr/bin/env python3
"""
Use the ansible_vault python library to encrypt and decrypt files

To use this script, you need to install the ansible-vault library:

    pip install ansible_vault

"""

import argparse
import sys
from getpass import getpass
import subprocess

from ansible_vault import Vault

# Define the vault password variable name in gopass
VPVAR = ".vault_pass-var"


def main():
    parser = argparse.ArgumentParser(
        description="Encrypt or decrypt a file using ansible-vault"
    )
    parser.add_argument(
        "-i", "--input_file", help="The file to encrypt or decrypt", required=True
    )
    parser.add_argument("-o", "--output_file", help="The output file", required=False)
    parser.add_argument("-e", "--encrypt", help="Encrypt the file", action="store_true")
    parser.add_argument("-d", "--decrypt", help="Decrypt the file", action="store_true")
    args = parser.parse_args()

    if args.encrypt and args.decrypt:
        print("You can't encrypt and decrypt at the same time")
        sys.exit(1)

    if not args.encrypt and not args.decrypt:
        print("You must specify either --encrypt or --decrypt")
        sys.exit(1)

    vault_password = getpass("Enter the vault password: ")
    with open(args.input_file, "r") as f:
        content = f.read()
    vault = Vault(vault_password)

    if args.encrypt:
        if args.output_file:
            with open(args.output_file, "w") as f:
                vault.dump_raw(content, f)
            print("File encrypted and saved to", args.output_file)
        else:
            vault.dump_raw(content, sys.stdout)
    elif args.decrypt:
        with open(args.input_file) as f:
            decrypted_content = vault.load_raw(f.read())
            decoded_content = decrypted_content.decode("utf-8")
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(decoded_content)
            print("File decrypted and saved to", args.output_file)
        else:
            print(decoded_content)


if __name__ == "__main__":
    main()
