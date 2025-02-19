from typing import Iterable
import scrapy
import json
from scrapy import Request


class AveragePointsSpider(scrapy.Spider):
    name = 'average_points'
    start_urls = ['https://www.transfermarkt.world']
    years_start = 2014 #inclusive
    years_end = 2025 #exclusive
    seen_team_ids = set()

    def start_requests(self) -> Iterable[Request]:
        with open("sorted_teams.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            link = item['Link_to_team'].replace("startseite", "leistungsdaten") + '/plus/0?reldata=%26'
            for year in range(self.years_start, self.years_end):
                url = f"https://www.transfermarkt.world{link}{year}"
                yield scrapy.Request(url, callback=self.parse, meta={'reldata': 260000 + year})

    def parse(self, response):
        year = response.meta['reldata'] - 260000
        TeamId = response.url.split("/")[-3]
        content_text = response.xpath('//p[@class="content"]/text()').get()

        if content_text:
            import re
            match = re.search(r'\d+,\d+', content_text)
            if match:
                average_points = match.group(0)
                yield {
                    'TeamID': TeamId,
                    'Year': year,
                    'AveragePoints': average_points,
                }

