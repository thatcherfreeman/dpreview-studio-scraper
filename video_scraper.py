import json
from typing import List, Dict, Tuple, Optional
import requests
import sys, os, time
from argparse import ArgumentParser

from stills_scraper import make_post_request, download_file, write_info


def get_payload(
    camera: Optional[str] = None,
    format_str: Optional[str] = None,
) -> Dict[str, str]:
    post_attributes = [
        {
            "instanceId": 29,
            "value": camera,
            "isSet": camera is not None,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
        {
            "instanceId": 72,
            "value": format_str,
            "isSet": format_str is not None,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
        {
            "instanceId": 421,
            "value": None,
            "isSet": False,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
    ]

    post_payload = {
        "sceneId": 9,
        "includeImages": True,
        "attributes": post_attributes,
    }
    return {"data": json.dumps(post_payload, separators=(",", ":"))}


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
    camera_list = [
        (value["displayValue"].split("/")[0].strip(), value["clientValue"])
        for value in response_dict["attributes"][0]["values"]
    ]
    for camera_display, camera in camera_list:
        directory = os.path.join("downloads", "video", camera_display)
        if os.path.exists(directory):
            print(f"Skipping {camera_display}")
            continue

        print(camera_display)
        # get formats for this camera.
        response_dict = make_post_request(get_payload(camera))
        formats_list = [
            value["clientValue"] for value in response_dict["attributes"][1]["values"]
        ]
        for format_str in formats_list:
            print(format_str)
            response_dict = make_post_request(get_payload(camera, format_str))
            originalUrlKey = response_dict["images"][0]["originalUrl"]
            s3key = originalUrlKey.split("s3Key=")[-1]
            extension = s3key.split(".")[-1]

            os.makedirs(directory, exist_ok=True)
            if download_file(
                originalUrlKey, os.path.join(directory, f"{format_str}.{extension}")
            ):
                write_info(
                    response_dict["images"][0]["infoText"],
                    os.path.join(directory, f"{format_str}_info.txt"),
                )

            num_downloads += 1
            if args.num_images > 0 and num_downloads >= args.num_images:
                print(f"Saved {num_downloads} images. Exiting.")
                sys.exit()
