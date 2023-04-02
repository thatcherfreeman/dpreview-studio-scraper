import json
from typing import List, Dict, Tuple, Optional
import requests
import sys, os, time
from argparse import ArgumentParser


def get_payload(
    lighting: Optional[str] = None,
    camera: Optional[str] = None,
    format_str: Optional[str] = None,
    iso: Optional[str] = None,
) -> Dict[str, str]:
    post_attributes = [
        {
            "instanceId": 18,
            "value": lighting,
            "isSet": lighting is not None,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
        {
            "instanceId": 13,
            "value": camera,
            "isSet": camera is not None,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
        {
            "instanceId": 15,
            "value": format_str,
            "isSet": format_str is not None,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
        {
            "instanceId": 16,
            "value": iso,
            "isSet": iso is not None,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
        {
            "instanceId": 126,
            "value": None,
            "isSet": False,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
        {
            "instanceId": 171,
            "value": None,
            "isSet": False,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
        {
            "instanceId": 199,
            "value": None,
            "isSet": False,
            "allowDefaultIfUnset": False,
            "isFixed": False,
        },
    ]

    post_payload = {
        "sceneId": 1,
        "includeImages": True,
        "attributes": post_attributes,
    }
    return {"data": json.dumps(post_payload, separators=(",", ":"))}


def make_post_request(payload: Dict[str, str]) -> Dict:
    post_url = "https://www.dpreview.com/reviews/image-comparison/get-images"
    headers = {
        "User-Agent": "PostmanRuntime/7.31.3",
    }
    s = requests.Session()
    request = requests.Request(
        "POST", post_url, headers=headers, data=payload
    ).prepare()
    time.sleep(0.5)
    response = s.send(request)
    while response.status_code == 429:
        print("Got status code 429, retrying in 1m...")
        time.sleep(60)
        response = s.send(request)
    assert response.status_code == 200, f"Got response code {response.status_code}"
    response_dict = json.loads(response.text)
    return response_dict


def download_file(originalUrlKey, fn):
    get_url = f"https://www.dpreview.com{originalUrlKey}"
    headers = {
        "User-Agent": "PostmanRuntime/7.31.3",
    }
    s = requests.Session()
    request = requests.Request("GET", get_url, headers=headers).prepare()
    response = s.send(request)
    while response.status_code == 429:
        print("Got status code 429, retrying in 1m...")
        time.sleep(60)
        response = s.send(request)
    assert response.status_code == 200, f"Got response code {response.status_code}"
    with open(fn, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--num-images",
        type=int,
        default=5,
        help="Number of files to download. Set to zero to download all, ddos protection god help you.",
    )
    args = parser.parse_args()

    num_downloads = 0

    response_dict = make_post_request(get_payload())
    lighting_scenarios = [
        value["clientValue"] for value in response_dict["attributes"][0]["values"]
    ]
    for lighting in lighting_scenarios:
        print(lighting)
        response_dict = make_post_request(get_payload(lighting))
        camera_list = [
            (value["displayValue"], value["clientValue"])
            for value in response_dict["attributes"][1]["values"]
        ]
        for camera_display, camera in camera_list:
            print(camera_display)
            # get formats for this camera.
            response_dict = make_post_request(get_payload(lighting, camera))
            formats_list = [
                value["clientValue"]
                for value in response_dict["attributes"][2]["values"]
            ]
            for format_str in formats_list:
                print(format_str)
                response_dict = make_post_request(
                    get_payload(lighting, camera, format_str)
                )
                iso_list = [
                    value["clientValue"]
                    for value in response_dict["attributes"][3]["values"]
                ]
                for iso in iso_list:
                    print(iso)
                    response_dict = make_post_request(
                        get_payload(lighting, camera, format_str, iso)
                    )
                    directory = os.path.join(
                        "downloads",
                        "stills",
                        lighting.lower(),
                        camera_display,
                        format_str.lower(),
                    )
                    originalUrlKey = response_dict["images"][0]["originalUrl"]
                    s3key = originalUrlKey.split("s3Key=")[-1]
                    extension = s3key.split(".")[-1]

                    os.makedirs(directory, exist_ok=True)
                    download_file(
                        originalUrlKey, os.path.join(directory, f"iso{iso}.{extension}")
                    )

                    with open(os.path.join(directory, f"iso{iso}_{format.lower()}_info.txt"), "w") as f:
                        f.write(response_dict["images"][0]["infoText"])
                    num_downloads += 1
                    if args.num_images > 0 and num_downloads >= args.num_images:
                        print(f"Saved {num_downloads} images. Exiting.")
                        sys.exit()
