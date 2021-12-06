"""
This module is to download subtitle from iQIYI
"""

import re
import os
import time
import shutil
import json
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from common.utils import find_visible_element_by_xpath, get_season_number, find_present_element_by_xpath, download_file, convert_subtitle, save_html


def download_subtitle(driver, output):
    web_content = find_present_element_by_xpath(
        driver, "//script[@id='__NEXT_DATA__']")
    try:
        data = json.loads(web_content.get_attribute('innerHTML'))
        drama = data['props']['initialState']

        if drama and 'album' in drama:
            info = drama['album']['videoAlbumInfo']
            if info:
                title = info['name'].strip()
                episode_num = info['originalTotal']
                if 'maxOrder' in info:
                    current_eps = info['maxOrder']
                else:
                    current_eps = episode_num
                season_search = re.search(r'(.+)第(.+)季', title)

                if season_search:
                    drama_name = season_search.group(1).strip()
                    season_name = get_season_number(season_search.group(2))
                else:
                    drama_name = title
                    season_name = '01'

                print(drama_name)

                if current_eps == episode_num:
                    print(
                        f"\n第{season_name}季 共有：{episode_num} 集\t下載全集\n---------------------------------------------------------------")
                else:
                    print(
                        f"\n第{season_name}季 共有：{episode_num} 集\t更新至 第{current_eps}集\t下載全集\n---------------------------------------------------------------")

            episode_list = []
            if 'cacheAlbumList' in drama['album'] and '1' in drama['album']['cacheAlbumList'] and len(drama['album']['cacheAlbumList']['1']) > 0:
                episode_list = drama['album']['cacheAlbumList']['1']
            elif 'play' in drama and 'cachePlayList' in drama['play'] and '1' in drama['play']['cachePlayList'] and len(drama['play']['cachePlayList']['1']) > 0:
                episode_list = drama['play']['cachePlayList']['1']

            folder_path = f'{output + drama_name}.S{season_name}'
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)

            if len(episode_list) > 0:
                for episode in episode_list:

                    if 'payMarkFont' in episode and episode['payMarkFont'] == 'Preview':
                        break
                    if 'order' in episode:
                        episode_name = str(episode['order']).zfill(2)
                    if 'albumPlayUrl' in episode:
                        episode_url = episode['albumPlayUrl'].replace(
                            '//', 'https://').replace('lang=en_us', 'lang=zh_tw').replace('lang=zh_cn', 'lang=zh_tw').strip()
                        # print(episode_url)

                        driver.get(episode_url)
                        time.sleep(2)

                        xml = ''
                        delay = 0
                        print(
                            f"尋找第 {int(season_name)} 季 第 {int(episode_name)} 集字幕中...")
                        logs = []
                        while not xml:
                            logs += driver.execute_script(
                                "return window.performance.getEntries();")
                            time.sleep(2)
                            xml = next((log for log in logs
                                        if re.search(r'\.xml', log['name'])), None)
                            delay += 1
                            if delay > 60:
                                print("找不到可下載的字幕，可用VPN換區到新加坡試看看")
                                driver.quit()
                                exit(1)

                        if xml:
                            subtitle_link = xml['name']
                            # print(subtitle_link)
                            file_name = f'{drama_name}.S{season_name}E{episode_name}.WEB-DL.iQiyi.zh-Hant.xml'
                            os.makedirs(os.path.dirname(
                                        f'{folder_path}/'), exist_ok=True)
                            download_file(subtitle_link, os.path.join(
                                folder_path, file_name))
                print()
                convert_subtitle(folder_path, 'iqiyi')
            driver.quit()

    except json.decoder.JSONDecodeError:
        print("String could not be converted to JSON")