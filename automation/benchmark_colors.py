import json
import os
from collections import OrderedDict
from io import StringIO
from pathlib import Path

import click
from colorteller import teller
from colorteller.utils import benchmark
from colorteller.visualize import BenchmarkCharts
from dateutil import parser
from dotenv import load_dotenv
from loguru import logger

load_dotenv("automation/.env")
history_file = "automation/add_new_entries.history"


@click.command()
@click.option("--data_file", "-d", type=click.Path(exists=True), help="data file path")
@click.option("--save_path", "-s", default="static/assets/colors/", help="Save path")
def main(data_file, save_path):
    """
    Benchmark colors
    """

    with open(data_file, "r") as f:
        data = json.load(f)

    hex_strings = data.get("hex")
    hex_strings = [f"#{x}" for x in hex_strings]

    ct = teller.ColorTeller(hex_strings=hex_strings)

    c = teller.Colors(colorteller=ct)

    m = c.metrics(
        methods=[benchmark.PerceptualDistanceBenchmark, benchmark.LightnessBenchmark]
    )

    filename = Path(data_file).name.strip(".json")

    target_folder = Path(save_path) / filename
    if not target_folder.exists():
        target_folder.mkdir(parents=True)

    charts = BenchmarkCharts(metrics=m, save_folder=target_folder)

    charts.distance_matrix(show=False, save_to=True)

    charts.noticable_matrix(show=False, save_to=True)


if __name__ == "__main__":

    main()

    logger.info("End of Game")
