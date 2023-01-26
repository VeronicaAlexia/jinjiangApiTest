import time
import src
import book
import argparse
import template
from instance import *
from lib import get_url_id

from concurrent.futures import ThreadPoolExecutor


def shell_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--download", nargs=1, default=None, help="please input book_id")
    parser.add_argument("-s", "--search", dest="search", nargs=1, default=None, help="search book by book name")
    parser.add_argument("-m", "--max", dest="threading_max", default=None, help="please input max threading")
    parser.add_argument("-up", "--update", default=False, action="store_true", help="update books")
    parser.add_argument("--login", default=None, nargs="+", help="login account")
    parser.add_argument("--epub", default=True, action="store_true", help="output epub file")
    parser.add_argument("--output", default="downloads", nargs="?", help="output epub file")
    parser.add_argument("--cache", default="cache", nargs="?", help="output epub file")

    Vars.current_command = parser.parse_args()
    if Vars.current_command.login:
        if len(Vars.current_command.login) >= 2:
            login_account(Vars.current_command.login[0], Vars.current_command.login[1])
        else:
            print("login failed, please input username and password")

    if Vars.current_command.update:
        if Vars.cfg.data['downloaded_book_id_list'] > 0:
            for book_id in Vars.cfg.data['downloaded_book_id_list']:
                get_book_info(book_id)
        else:
            print("no book downloaded, please download book first.")

    if Vars.current_command.search:
        if Vars.current_command.search[0] != '':
            search_book(Vars.current_command.search[0])
        else:
            print("search book name is empty")

    if Vars.current_command.threading_max:
        if str(Vars.current_command.max).isdigit():
            Vars.threading_max = int(Vars.current_command.max)
            Vars.cfg.save()
        else:
            print("threading_max is not digit:", Vars.current_command.max)

    if Vars.current_command.download:
        shell_download_book(Vars.current_command.download[0])


@get_url_id()
def shell_download_book(bookid: str):
    try:
        Vars.current_book = src.Book.novel_basic_info(bookid)
        if Vars.current_book is not None:
            file_name_list = get_book_info(Vars.current_book)
            output_text_and_epub_file(Vars.current_book, file_name_list)
        else:
            print("bookid is not exist:", bookid)
    except Exception as e:
        print("download book error:", e)


def get_book_info(book_info):
    current_book = book.Book(book_info)  # create book object from book information.
    current_book.start_download_book_and_get_detailed()  # start download book
    print(current_book.book_detailed)
    with ThreadPoolExecutor(max_workers=32) as executor:
        for chapter in src.Book.get_chapter_list(book_info.novelId):  # type: template.ChapterInfo
            if chapter.isvip == 0:
                executor.submit(current_book.download_no_vip_content, chapter)
            else:
                # vip chapter isvip is 2
                executor.submit(current_book.download_vip_content, chapter)
    time.sleep(3)  # wait for all thread finish.
    set_file_name_list = []
    for file_name in os.listdir(Vars.current_command.cache):
        if file_name.find(book_info.novelId) != -1:
            set_file_name_list.append(file_name)

    set_file_name_list.sort(key=lambda x: int(x.split("-")[1]))  # sort file name by chapter id number.
    return set_file_name_list


def output_text_and_epub_file(book_info, file_name_list):
    with open(f"{Vars.current_command.output}/{book_info.novelName}/{book_info.novelName}.txt", "a",
              encoding="utf-8") as f2:
        for index, file_name in enumerate(file_name_list):
            with open(f"{Vars.current_command.cache}/{file_name}", "r", encoding="utf-8") as f:
                # content = f.read()
                # chapter_title = content.split("\n")[0]
                f2.write(f"\n\n\n第{index}章 " + f.read())

    command_line = f"-file {Vars.current_command.output}/{book_info.novelName}/{book_info.novelName}.txt " \
                   f"-o {Vars.current_command.output}/{book_info.novelName} " \
                   f"-cover {book_info.novelCover}"

    if Vars.current_command.epub:
        if os.name == 'nt':
            os.system(f"epub_windows_x64.exe " + command_line)
        elif os.name == 'posix':
            os.system(f"./epub_linux_x64 " + command_line)
        else:
            print("not support os, please use windows or linux x64")
        # epub_book.epub_file_export()
        # current_book.show_download_results()  # show download results after download.
        # current_book.out_put_text_file()  # output book content to text file.
        # current_book.set_downloaded_book_id_in_list()  # set book id in downloaded book list.
        #
        # if current_book.multi_thread_download_content():  # download book content with multi thread.
        #     current_book.show_download_results()  # show download results after download.
        #     current_book.out_put_text_file()  # output book content to text file.
        #     current_book.set_downloaded_book_id_in_list()  # set book id in downloaded book list.
        # else:
        #     print(f"download bookid:{bookid} failed, please try again.")


def search_book(search_name: str, next_page: int = 0):
    if search_name is None:
        return False
    response = src.app.Book.search_info(keyword=search_name, page=next_page)
    if response.get("code") == '200':
        for index, book_info in enumerate(response["data"]):
            print("index:", index, "novelId:", book_info["novelId"], "novelName:", book_info["novelName"])
        print("next page:[next or n]\t previous page:[previous or p], exit:[exit or e]")
        input_index = input("please input search index:")
        if str(input_index).isdigit() and int(input_index) < len(response["data"]):
            get_book_info(response["data"][int(input_index)]["novelId"])
        elif input_index == "next" or input_index == "n":
            search_book(search_name=search_name, next_page=next_page + 1)
        elif input_index == "previous" or input_index == "p":
            if next_page > 0:
                search_book(search_name=search_name, next_page=next_page - 1)
            else:
                print("no previous page!")
        elif input_index == "exit" or input_index == "e":
            return False
        else:
            print("input index is not digit or out of range, please input again.")
    else:
        print("search failed", response["message"])


def login_account(username: str, password: str):
    response = src.app.Account.login(username, password)
    if response.get("message") is None:
        print("login success", response["nickName"], "vip:", response["readergrade"])
        Vars.cfg.data['user_info'] = {
            "nickName": response["nickName"],
            "token": response["token"],
            "readerId": response["readerId"],
            "balance": response["balance"],
            "readergrade": response["readergrade"]
        }
        Vars.cfg.save()
    else:
        print("login failed", response["message"])


if __name__ == '__main__':
    set_config()
    try:
        shell_parser()
    except KeyboardInterrupt:
        print("\n exit program by keyboard interrupt")
