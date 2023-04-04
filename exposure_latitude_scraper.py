import json
from typing import List, Dict, Tuple, Optional
import requests
import sys, os, time
from argparse import ArgumentParser

from stills_scraper import make_post_request, download_file, write_info


def get_payload(
    camera: Optional[str] = None,
    exposure: Optional[str] = None,
    shutter: Optional[str] = None,
    shot_mode: Optional[str] = None,
) -> Dict[str, str]:
    post_attributes = [
        {
            "instanceId": 144,
            "value": camera,
            "isSet": camera is not None,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
        {
            "instanceId": 146,
            "value": exposure,
            "isSet": exposure is not None,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
        {
            "instanceId": 177,
            "value": shutter,
            "isSet": shutter is not None,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
        {
            "instanceId": 178,
            "value": None,
            "isSet": False,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
        {
            "instanceId": 404,
            "value": shot_mode,
            "isSet": shot_mode is not None,
            "allowDefaultIfUnset": True,
            "isFixed": False,
        },
    ]
    post_payload = {
        "sceneId": 45,
        "includeImages": True,
        "attributes": post_attributes,
    }
    return {"data": json.dumps(post_payload, separators=(",", ":"))}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--num-images",
        type=int,
        default=10,
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
        camera_directory = os.path.join(
            "downloads", "exposure_latitude", camera_display
        )
        if os.path.exists(camera_directory):
            print(f"Skipping {camera_display}")
            continue

        print(camera_display)
        # get exposures for this camera.
        response_dict = make_post_request(get_payload(camera))
        exposures_list = [
            (
                value["displayValue"]
                .replace("|", "-")
                .split("(")[0]
                .replace("/", "_")
                .strip(),
                value["clientValue"],
            )
            for value in response_dict["attributes"][1]["values"]
            if value is not None
        ]
        for exposure_display, exposure in exposures_list:
            print(exposure_display)
            response_dict = make_post_request(get_payload(camera, exposure))

            # Get shutter options for this camera, not always available.
            mode_list: List[Tuple[Optional[str], Optional[str], Optional[str]]] = [
                (None, None, None)
            ]
            if response_dict["attributes"][2]["values"][0] is not None:
                # Shutter type is not None
                mode_list = [
                    (
                        value["displayValue"].replace("|", "-").strip(),
                        value["clientValue"],
                        "shutter",
                    )
                    for value in response_dict["attributes"][2]["values"]
                ]
            if response_dict["attributes"][4]["values"][0] is not None:
                assert (
                    response_dict["attributes"][2]["values"][0] is None
                ), "Should have null shutter mode if shot mode is not none."
                # Single shot vs High res
                mode_list = [
                    (
                        value["displayValue"].replace("|", "-").strip(),
                        value["clientValue"],
                        "shot_mode",
                    )
                    for value in response_dict["attributes"][4]["values"]
                ]

            for mode_display, mode_client, mode_type in mode_list:
                # Need to try all shutter options, if they exist.
                file_directory = camera_directory
                if mode_type == "shutter":
                    print(mode_display)
                    response_dict = make_post_request(
                        get_payload(camera, exposure, shutter=mode_client)
                    )
                    file_directory = os.path.join(camera_directory, mode_display)
                if mode_type == "shot_mode":
                    print(mode_display)
                    response_dict = make_post_request(
                        get_payload(camera, exposure, shot_mode=mode_client)
                    )
                    file_directory = os.path.join(camera_directory, mode_display)

                # In this API, the raws and JPEGs are provided simultaneously in originalUrl and displayImageUrl
                # Download RAW
                raw_originalUrlKey = response_dict["images"][0]["originalUrl"]
                raw_s3key = raw_originalUrlKey.split("s3Key=")[-1]
                raw_extension = raw_s3key.split(".")[-1]
                raw_fn = f"{exposure_display}.{raw_extension}"
                os.makedirs(file_directory, exist_ok=True)
                downloaded_raw = download_file(
                    raw_originalUrlKey, os.path.join(file_directory, raw_fn)
                )

                # Download JPEG
                jpg_urlKey = response_dict["images"][0]["displayImageUrl"]
                jpg_s3key = jpg_urlKey.split("s3Key=")[-1]
                jpg_extension = jpg_s3key.split(".")[-1]
                jpg_fn = f"{exposure_display}.{jpg_extension}"
                downloaded_jpg = download_file(
                    jpg_urlKey, os.path.join(file_directory, jpg_fn)
                )

                if downloaded_raw or downloaded_jpg:
                    info_txt_fn = (
                        f"{exposure_display}_info.txt"
                        if mode_display is not None
                        else f"{exposure_display}_info.txt"
                    )
                    write_info(
                        response_dict["images"][0]["infoText"],
                        os.path.join(file_directory, info_txt_fn),
                    )

                num_downloads += 1 if downloaded_raw else 0
                num_downloads += 1 if downloaded_jpg else 0
                if args.num_images > 0 and num_downloads >= args.num_images:
                    print(f"Saved {num_downloads} images. Exiting.")
                    sys.exit()
