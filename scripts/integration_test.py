"""
====================================================
Project : Converigo
Author  : Pico Lala & ChatGPT

Integration Test Runner
Version : 2.4.0

Purpose:
- Discover plugins correctly
- Test homepage
- Test recommendation endpoint
- Test conversion matrix
- Generate JSON report

Run:
python -m scripts.integration_test
====================================================
"""


import json

from pathlib import Path

from fastapi.testclient import TestClient


from app.main import app

from app.plugins.registry import registry





client = TestClient(app)



REPORT_PATH = Path(
    "tests/integration/report.json"
)


TEST_FILES_DIR = Path(
    "test_files"
)




MATRIX = [

    ("jpg", "png"),

    ("jpg", "webp"),

    ("png", "jpg"),

    ("png", "webp"),

    ("png", "ico"),

    ("webp", "jpg"),

    ("webp", "png"),

    ("mp3", "wav"),

    ("mp4", "mp3"),

]






def normalize_plugins():

    """
    Convert registry data into:

    [
        {
            source:"jpg",
            target:"webp",
            slug:"jpg-to-webp"
        }
    ]

    """


    result = []



    for item in registry.plugins:


        if isinstance(item, tuple):


            source = item[0]

            target = item[1]

            plugin = item[-1]



            slug = (

                f"{source}-to-{target}"

            )



            result.append({

                "source": source,

                "target": target,

                "slug": slug,

                "plugin": plugin

            })



        else:


            slug = getattr(

                item,

                "slug",

                str(item)

            )


            result.append({

                "slug": slug,

                "plugin": item

            })



    return result







def discover_plugins():


    print("=" * 60)

    print("PLUGIN DISCOVERY")

    print("=" * 60)



    plugins = normalize_plugins()



    result = []



    for plugin in plugins:


        print(

            "[OK]",

            plugin["slug"]

        )



        result.append(

            plugin["slug"]

        )



    print("=" * 60)

    print(

        "TOTAL PLUGINS :",

        len(result)

    )

    print("=" * 60)



    return result







def test_home():


    response = client.get("/")


    return {


        "status":

            response.status_code,


        "ok":

            response.status_code == 200

    }








def find_sample(extension):


    if not TEST_FILES_DIR.exists():

        return None



    for file in TEST_FILES_DIR.iterdir():


        if (

            file.suffix

            .lower()

            .replace(".","")

            == extension.lower()

        ):

            return file



    return None







def test_recommend(source):


    try:


        response = client.get(

            f"/recommend/{source}"

        )


        return {


            "source":

                source,


            "status":

                response.status_code,


            "body":

                response.json()

        }



    except Exception as e:


        return {


            "source":

                source,


            "error":

                str(e)

        }









def check_plugin(

    source,

    target

):


    plugins = normalize_plugins()



    for plugin in plugins:


        if (

            plugin.get("source")

            == source

            and

            plugin.get("target")

            == target

        ):

            return True



    return False







def test_conversion(

    source,

    target

):


    result = {


        "source":

            source,


        "target":

            target

    }



    if not check_plugin(

        source,

        target

    ):


        result["status"] = (

            "SKIPPED - plugin missing"

        )


        result["plugin_available"] = False


        return result





    result["plugin_available"] = True




    sample = find_sample(

        source

    )



    if not sample:


        result["status"] = (

            "SKIPPED - sample missing"

        )


        return result







    try:


        with open(

            sample,

            "rb"

        ) as f:



            response = client.post(

                "/convert",


                files={


                    "file": (

                        sample.name,

                        f,

                        "application/octet-stream"

                    )

                },


                data={


                    "target_format":

                        target

                }

            )



        result["status_code"] = (

            response.status_code

        )


        result["response"] = (

            response.json()

        )





    except Exception as e:


        result["error"] = str(e)





    return result










def run_tests():


    report = {}



    report["plugins"] = (

        discover_plugins()

    )



    report["home"] = (

        test_home()

    )



    report["recommendations"] = []



    for source, target in MATRIX:


        report["recommendations"].append(

            test_recommend(source)

        )





    report["conversions"] = []



    for source, target in MATRIX:



        print(

            "Testing:",

            source,

            "->",

            target

        )



        report["conversions"].append(

            test_conversion(

                source,

                target

            )

        )






    REPORT_PATH.parent.mkdir(

        parents=True,

        exist_ok=True

    )



    with open(

        REPORT_PATH,

        "w",

        encoding="utf-8"

    ) as file:


        json.dump(

            report,

            file,

            indent=4,

            ensure_ascii=False

        )




    print()

    print(

        "REPORT SAVED:"

    )

    print(

        REPORT_PATH

    )







if __name__ == "__main__":


    run_tests()