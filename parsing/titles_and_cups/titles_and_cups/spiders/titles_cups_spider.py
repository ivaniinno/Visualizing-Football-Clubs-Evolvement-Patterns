from typing import Iterable
import scrapy
import json
from scrapy import Request


class AveragePointsSpider(scrapy.Spider):
    name = 'titles_cups'
    start_urls = ['https://www.transfermarkt.world']
    years_start = 2014  # inclusive
    years_end = 2025  # exclusive

    def start_requests(self) -> Iterable[Request]:
        with open("sorted_teams.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            link = item['Link_to_team'].replace("startseite", "erfolge")
            for year in range(self.years_start, self.years_end):
                url = f"https://www.transfermarkt.world{link}"
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        TeamId = response.url.split("/")[-1]
        cups_num = 0

        for box in response.xpath('//div[@class="large-6 columns"]/div[@class="box"]'):
            cups_num += int(box.xpath('.//div[@class="header"]/h2/text()').get().strip().split(" ")[0][:-1])

        titles_in_years = {}

        for row in response.xpath('//tr'):
            season = row.xpath('.//td[@class="zentriert"]/text()').get()
            if season:
                season = season.strip()
                if "/" in season:
                    year = season.split("/")[0]
                else:
                    year = season

                if len(year) == 2:
                    year = int(year) + 2000
                else:
                    year = int(year)

                if year < self.years_start:
                    break
                if year < self.years_end:
                    if year not in titles_in_years:
                        titles_in_years[year] = 1
                    else:
                        titles_in_years[year] += 1

        yield {
            'TeamID': TeamId,
            'NumberOfTitlesByYears': titles_in_years,
            'NumberOfCups': cups_num,
        }
