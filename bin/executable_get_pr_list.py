#!/usr/bin/env python
import os

import pandas as pd
from tabulate import tabulate


def split_slash(astring):
    return astring.split("/")


os.system("gh pr list --json files,number,author,createdAt >/tmp/prs.json")
os.system(
    "jq '[.[] | . as $item | .files[] | {authorLogin: $item.author.login, createdAt: $item.createdAt, filePath: .path, number: $item.number}]' /tmp/prs.json >/tmp/prs_flat.json"
)


df = pd.read_json("/tmp/prs_flat.json")
df[["group", "file"]] = df["filePath"].str.split("/", expand=True)
dfgb = df.groupby("file").agg(
    {
        "authorLogin": lambda x: ", ".join(sorted(set(x))),
        "createdAt": "min",
        "group": "first",
        "number": lambda x: ", ".join(sorted(set(str(x) for x in x))),
    }
)
dfgb.rename(
    columns={
        "authorLogin": "Authors",
        "createdAt": "First Created",
        "group": "Tower",
        "number": "PR Numbers",
    },
    inplace=True,
)
dfgb.reset_index(inplace=True)
dfgb.rename(columns={"file": "File"}, inplace=True)
dfgb = dfgb.reindex(["Tower", "File", "PR Numbers", "Authors", "First Created"], axis=1)
dfgb.sort_values(
    by=["Tower", "File"],
    inplace=True,
)
print(
    tabulate(dfgb, headers="keys", tablefmt="psql", showindex=False)
    if not df.empty
    else "No PRs found"
)
