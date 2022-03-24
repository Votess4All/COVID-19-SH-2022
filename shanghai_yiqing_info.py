from bs4 import BeautifulSoup

import pandas as pd
import requests
import numpy as np


def spilt_list_into_batch(a, n=10):
    return [a[i:i + n] for i in range(0, len(a), n)]


def get_lat_and_lon(location, key):
    """
    这里主要调用的是高德的地理编码接口，具体参数可以参考这个链接
    https://lbs.amap.com/api/webservice/guide/api/georegeo，
    web端key的获取也可以参考他们相关的文档，
    """

    json_body = {
        "address": location,
        "output": "XML",
        "key": key,
        "batch": True if "|" in location else False
    }
    r = requests.post(
        "https://restapi.amap.com/v3/geocode/geo", data=json_body)

    lats_and_lons = []
    for geocode in r.json()["geocodes"]:
        lats_and_lons.append(list(map(float, geocode["location"].split(","))))

    return lats_and_lons


def get_city_disease_info(
        shanghaifabu_url="https://mp.weixin.qq.com/s/w8UqtdmBtdLQitM7emOVjw",
        city_name="上海市"):
    """
    给定一篇上海发布的文章，找到相关区内公布的具体无感染人群所在地址
    """

    r = requests.get(shanghaifabu_url)
    demo = r.text

    soup = BeautifulSoup(demo, 'html.parser')
    location_div = soup.find("div", attrs={"class": "rich_media_content"})
    locate_section_div = location_div.findAll(
        "section", attrs={"data-role": "title"})

    city_area_street = {f"{city_name}": []}
    for i, sub_div in enumerate(locate_section_div):
        area_name = sub_div.find("strong").text
        ps = sub_div.findAll("p")

        area_xiaoqu = []
        for j, area_ps in enumerate(ps):
            if j <= 1 or j >= len(ps)-2:
                continue

            area_xiaoqu.append(f"{city_name}"+area_name +
                               area_ps.text.strip("，"))
        city_area_street[f"{city_name}"].append({area_name: area_xiaoqu})

    return city_area_street


def save_info_to_dir(city_name="上海市"):
    city_qu_jiedao = get_city_disease_info()
    shanghai_info = city_qu_jiedao[city_name]

    dfs = []
    for q, qu in enumerate(shanghai_info):

        df_list = []
        for key, value in qu.items():

            jiedaos = value
            batch_jiedaos = spilt_list_into_batch(jiedaos)
            lats_and_lons = []
            for batch in batch_jiedaos:
                address = "|".join(batch)
                lats_and_lons.extend(get_lat_and_lon(address))

        for i, (jiedao, lat_and_lon) in enumerate(list(zip(jiedaos, lats_and_lons))):
            df_list.append({
                "ch_name": jiedao,
                "city": city_name,
                "lat_and_lon": ",".join(map(str, list(lats_and_lons[i])))
            })

        df = pd.DataFrame(df_list, columns=df_list[0].keys())
        df.to_csv(f"~/{key}.csv", index=False, encoding='gbk')

        dfs.extend(df_list)

    df = pd.DataFrame(dfs, columns=dfs[0].keys())
    df.to_csv(f"~/{city_name}.csv", index=False, encoding='gbk')
