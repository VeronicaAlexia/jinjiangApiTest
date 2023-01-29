import os
import re
import time

# from . import *
from lib import GET
from tqdm import tqdm
from . import UrlConstant
from instance import Vars
import template
from rich import print


@GET(UrlConstant.NOVEL_INFO)
def novel_basic_info(response: dict) -> template.BookInfo:  # get book information by novel_id
    if response.get("message") is None:  # get book information success then print book information.
        return template.BookInfo(**response)  # create book object from book information.
        # print book information with book detail.
    else:
        print("get book information failed, please try again.", response.get("message"))


@GET(UrlConstant.SEARCH_INFO)
def search_home_page(response: dict) -> [dict, None]:  # search book by keyword
    if response.get("code") == '200':
        return response.get("data")
    else:
        print("search failed:", response.get("message"))


@GET("getUserCenter")
def get_user_center(response: dict) -> [dict, None]:
    if not response.get("message"):
        return response
    else:
        print("get user info failed:", response.get("message"))


@GET("getAppUserinfo")
def get_user_info(response: dict) -> [dict, None]:
    if not response.get("message"):
        return response
    else:
        print("get user info failed:", response.get("message"))


@GET("search")
def search_book(response: dict):  # search book by keyword
    novel_info_list = []
    if response.get("items"):
        for index, novel_info in enumerate(response.get("items")):
            novel_info_list.append(template.SearchInfo(**novel_info))
    else:
        if response.get("message") == "没有更多小说了！":
            return response.get("message")
        else:
            print("search failed:", response.get("message"))

    return novel_info_list


@GET(UrlConstant.CHAPTER_LIST)
def get_chapter_list(response):  # get chapter list by novel_id
    if response.get("message"):
        print("get chapter list failed, please try again.", response.get("message"))
        return None
    download_content = []
    for chapter in tqdm(response['chapterlist'], ncols=100):
        chap_info = template.ChapterInfo(**chapter)
        chap_info.chaptername = re.sub(r'[\\/:*?"<>|]', '', chap_info.chaptername)
        chap_info.cache_file_path = os.path.join(Vars.current_command.cache,
                                                 chap_info.novelid + "-" +
                                                 chap_info.chapterid + "-" +
                                                 chap_info.chaptername + ".txt"
                                                 )
        if not os.path.exists(chap_info.cache_file_path):
            if chap_info.originalPrice == 0:
                download_content.append(chap_info)
            else:
                if Vars.cfg.data.get("token"):
                    download_content.append(chap_info)
    return download_content


@GET("chapterContent")
def get_chapter_vip_content(response) -> dict:
    try:
        return response
    except Exception as e:
        print(e)


@GET(UrlConstant.CONTENT)
def get_chapter_free_content(response) -> dict:
    try:
        return response
    except Exception as e:
        print(e)
