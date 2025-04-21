from typing import Iterable
import scrapy
import json
from scrapy import Request


class ClubImages(scrapy.Spider):
    name = 'club_images'
    start_urls = ['https://www.transfermarkt.world']

    def start_requests(self) -> Iterable[Request]:
        with open("sorted_teams.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            link = item['Link_to_team']
            id = item['TeamID']
            url = f"https://www.transfermarkt.world{link}"
            yield scrapy.Request(url, callback=self.parse, meta={'id': id})

    def parse(self, response):
        TeamId = response.meta['id']

        img_link = response.xpath('.//header[@class="data-header"]/div[@class="data-header__profile-container"]/img/@src').get()
        yield {
            'TeamID ': TeamId,
            'ImageLink': img_link
        }





