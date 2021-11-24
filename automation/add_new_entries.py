import json
import os
from collections import OrderedDict
from io import StringIO
from pathlib import Path

import click
import requests
import ruamel.yaml as yaml
from colorteller import teller
from colorteller.utils import benchmark
from colorteller.visualize import BenchmarkCharts
from dateutil import parser
from dotenv import load_dotenv
from loguru import logger
from ruamel.yaml.representer import RoundTripRepresenter

load_dotenv("automation/.env")
history_file = "automation/add_new_entries.history"

# Add representer to ruamel.yaml for OrderedDict
class MyRepresenter(RoundTripRepresenter):
    pass


yaml.add_representer(
    OrderedDict, MyRepresenter.represent_dict, representer=MyRepresenter
)
yaml = yaml.YAML()
yaml.Representer = MyRepresenter

# https://api.netlify.com/api/v1/sites/%7Bsite_id%7D/forms
NETLIFY_SITE_ID = os.getenv("NETLIFY_SITE_ID")
FORM_API_URI = f"https://api.netlify.com/api/v1/sites/{NETLIFY_SITE_ID}/forms"


def convert_title_to_filename(title, extras=None):
    """Converts the title of the tool to a good file name"""
    if extras is None:
        extras = "-_.()"
    valid_chars = lambda x: x.isalpha() or x.isdigit() or (x in extras)
    title_no_space = "-".join(title.split(" ")).lower()
    keep_valid_chars = lambda x: x if valid_chars(x) else "_"
    new_title = "".join([keep_valid_chars(x) for x in title_no_space])

    return new_title


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class Colors:
    def __init__(
        self, form_item=None, save_path=None, json_path=None, benchmark_path=None
    ):

        if form_item:
            self.data = self._parse_form_data(form_item)
        else:
            raise Exception("Please specify the source of data")

        if save_path is None:
            raise Exception("Please specify the save path")

        self.save_path = save_path
        self.json_path = json_path
        self.benchmark_path = benchmark_path

    def _parse_form_data(self, form_item):
        """ "
        here is an example of the data field.
        data": {
            "author": "LM",
            "name": "cat",
            "hex": "#208eb7,#8bd0eb,#214a65,#52dcbc",
            "email": "hi@leima.is",
            "summary": "This is a color palette generated by cologorical.",
            "ip": "162.158.88.184",
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36",
            "referrer": "https://colorteller.kausalflow.com/submit/"
        }
        """

        dt_iso = parser.parse(form_item.get("created_at")).date().isoformat()

        palette = {}
        form_data = form_item.get("data")

        palette["_id"] = form_item.get("id")
        palette["date"] = form_item.get("created_at")
        palette["date_iso"] = dt_iso

        schema = [
            {"key": "author"},
            {"key": "name"},
            {"key": "name", "target": "title"},
            {"key": "hex", "transform": self._parse_hex},
            {
                "key": "hex",
                "target": "colors",
                "transform": self._calculate_colors_fields,
            },
            # {"key": "email"},
            {"key": "summary"},
        ]

        palette_transformed = self._transform_on_schema(form_data, schema)

        palette.update(palette_transformed)

        return palette

    def _transform_on_schema(self, data, schema):
        """
        Transform the data according to the schema
        """

        res = {}
        for s in schema:
            s_k = s["key"]
            logger.debug(f"Getting {s_k}")
            s_v = data.get(s_k)
            if s.get("transform"):
                s_transform = s.get("transform")
                s_v = s_transform(s_v)
            s_target = s.get("target", s_k)

            res[s_target] = s_v

        return res

    def _parse_hex(self, hex_string):
        """
        Parse the hex string and return a list of hex color

        `#208eb7,#8bd0eb,#214a65,#52dcbc`
        """

        # validation
        if not isinstance(hex_string, str):
            raise Exception("Invalid hex strings")
        else:
            hex_string = hex_string.strip()

        if hex_string.startswith("["):
            hex_string = hex_string.strip("[").strip("]")

        hex_list = hex_string.split(",")

        hex_list_clean = []
        for h in hex_list:
            h = h.strip()
            if not h.startswith("#"):
                logger.error("Invalid hex string")
            h = h.strip("#")
            hex_list_clean.append(h)

        return hex_list_clean

    def _calculate_colors_fields(self, hex_strings):
        """Construct the color field being used in the website"""

        hex_list = self._parse_hex(hex_strings)

        colors = []
        for h in hex_list:
            colors.append({"hex": f"#{h}"})

        return colors

    def _filename(self):
        title = self.data.get("title", "")
        # date_iso = self.data.get("date_iso", "")
        hex_strings = "_".join(self.data.get("hex", ["palette"]))
        submission_id = self.data.get("_id", "")
        filename = convert_title_to_filename(
            "__".join([hex_strings, title, submission_id])
        )

        return filename

    def _save_yaml(self):
        res = None

        target = os.path.join(self.save_path, self._filename() + ".yaml")

        if os.path.isfile(target):
            logger.debug("Color already created!")
            res = {"status": "exist"}
        else:
            with open(target, "w+") as fp:
                yaml.dump(OrderedDict(self.data), fp)
            logger.info(f"Added a new tool {self.data.get('_id')}")
            res = {"status": "added", "_id": self.data.get("_id")}

        return res

    def _save_md(self):
        res = None

        md_file = self._filename() + ".md"
        target = os.path.join(self.save_path, md_file)

        if os.path.isfile(target):
            logger.debug("Color already created!")
            res = {"status": "exist"}
        else:
            logger.debug(f"Saving markdown to {md_file}")
            string_stream = StringIO()
            yaml.dump(OrderedDict(self.data), string_stream)
            md_content = string_stream.getvalue()
            string_stream.close()
            logger.debug(f"Markdown content: {md_content}")

            with open(target, "w+") as fp:
                logger.debug(f"Writing... to {md_file}")
                fp.write("---\n" + md_content + "\n---")
            logger.info(f"Added a new color palette {self.data.get('_id')}")
            res = {
                "status": "added",
                "_id": self.data.get("_id"),
                "title": self.data.get("title"),
            }

        return res

    def _save_json(self):
        if self.json_path is None:
            logger.error(
                f"saving json is special and please specify which folder to save the file to: json_path"
            )
            raise Exception("Please specify the json_path")
        json_file = self._filename() + ".json"
        if not os.path.exists(self.json_path):
            try:
                logger.debug(f"Creating folder {self.json_path}")
                os.makedirs(self.json_path, exist_ok=False)
            except Exception as e:
                pass
        target = os.path.join(self.json_path, json_file)

        if os.path.isfile(target):
            logger.debug("Color already created!")
            status = {"status": "exist"}
        else:
            with open(target, "w+") as fp:
                json.dump(self.data, fp)
            status = {
                "status": "added",
                "_id": self.data.get("_id"),
                "title": self.data.get("title"),
            }

        return status

    def _save_benchmark(self):
        if self.benchmark_path is None:
            logger.error(
                f"saving json is special and please specify which folder to save the file to: json_path"
            )
            raise Exception("Please specify the benchmark_path")

        hex_strings = self.data.get("hex")
        hex_strings = [f"#{x}" for x in hex_strings]

        ct = teller.ColorTeller(hex_strings=hex_strings)

        c = teller.Colors(colorteller=ct)

        m = c.metrics(
            methods=[
                benchmark.PerceptualDistanceBenchmark,
                benchmark.LightnessBenchmark,
            ]
        )

        filename = self._filename()
        target_folder = Path(self.benchmark_path) / filename
        if not target_folder.exists():
            target_folder.mkdir(parents=True)

        charts = BenchmarkCharts(metrics=m, save_folder=target_folder)

        charts.distance_matrix(show=False, save_to=True)

        charts.noticable_matrix(show=False, save_to=True)

        status = {
            "status": "added",
            "_id": self.data.get("_id"),
            "title": self.data.get("title"),
        }

        return status

    def save(self, type="md"):

        res = {}
        if type == "yaml":
            res = self._save_yaml()
        elif type == "md":
            res = self._save_md()
        elif type == "json":
            res = self._save_json()
        elif type == "benchmark":
            res = self._save_benchmark()

        return res


@click.command()
@click.option(
    "--netlify_api_base_url",
    default="https://api.netlify.com/api/v1/forms/",
    help="netlify form API base URL",
)
@click.option(
    "--netlify_form_id", default=os.getenv("NETLIFY_FORM_ID"), help="Netlify site ID"
)
@click.option("--token", default=os.getenv("NETLIFY_TOKEN"), help="NETLIFY API token")
@click.option("--save_path", default="content/colors/", help="Save path")
@click.option("--json_path", default="data/colors/", help="json file path")
@click.option("--benchmark_path", default="static/assets/colors/", help="Benchmark path")
def main(netlify_api_base_url, netlify_form_id, token, save_path, json_path, benchmark_path):

    netlify_api_base_url = f"{netlify_api_base_url}{netlify_form_id}/submissions"

    if not token:
        raise Exception("Please specify the Typeform API token")

    req = requests.get(netlify_api_base_url, auth=BearerAuth(token))

    tf_json = req.json()

    logger.info(f"{len(tf_json)} submissions in total")

    with open(history_file, "r") as fp:
        pr_history = fp.readlines()
    pr_history = [i.strip() for i in pr_history]

    logger.info(f"PR History: {pr_history}")

    for color in tf_json:
        colors_obj = Colors(form_item=color, save_path=save_path, json_path=json_path, benchmark_path=benchmark_path)
        if colors_obj.data.get("_id") not in pr_history:
            colors_save = colors_obj.save()
            colors_save_json = colors_obj.save(type="json")
            colors_save_benchmark = colors_obj.save(type="benchmark")
            if colors_save.get("status") == "added":
                with open(history_file, "a") as fp:
                    fp.write(f"{colors_save.get('_id')}\n")
                break


if __name__ == "__main__":

    test_response = """[
        {
            "site_id": "c7e03dca-189b-4099-8033-a5a09df3f602",
            "name": "kausalflow-colors-submission",
            "paths": null,
            "submission_count": 1,
            "fields": [
                {
                    "name": "bot-field",
                    "type": null
                },
                {
                    "name": "author",
                    "type": "text"
                },
                {
                    "name": "name",
                    "type": "text"
                },
                {
                    "name": "hex",
                    "type": "text"
                },
                {
                    "name": "email",
                    "type": "email"
                },
                {
                    "name": "summary",
                    "type": "textarea"
                }
            ],
            "created_at": "2021-11-24T10:25:28.996Z",
            "last_submission_at": "2021-11-24T10:35:18.281+00:00",
            "id": "619e13184f4a9c0008135770",
            "honeypot": true,
            "recaptcha": false
        },
        {
            "site_id": "c7e03dca-189b-4099-8033-a5a09df3f602",
            "name": "simpleContactForm",
            "paths": null,
            "submission_count": 1,
            "fields": [
                {
                    "name": "bot-field",
                    "type": null
                },
                {
                    "name": "author",
                    "type": "text"
                },
                {
                    "name": "name",
                    "type": "text"
                },
                {
                    "name": "hex",
                    "type": "text"
                },
                {
                    "name": "email",
                    "type": "email"
                },
                {
                    "name": "summary",
                    "type": "textarea"
                }
            ],
            "created_at": "2021-11-24T10:17:44.328Z",
            "last_submission_at": "2021-11-24T10:21:06.701+00:00",
            "id": "619e1148ad76d800087b0f1c",
            "honeypot": true,
            "recaptcha": false
        }
    ]"""

    main()

    logger.info("End of Game")
