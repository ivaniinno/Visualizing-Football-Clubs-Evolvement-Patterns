from typing import Iterable
import scrapy
import json
from scrapy import Request


class AveragePointsSpider(scrapy.Spider):
    name = 'kader_spider'
    start_urls = ['https://www.transfermarkt.world']
    years_start = 2014 #inclusive
    years_end = 2025 #exclusive
    seen_team_ids = set()

    def start_requests(self) -> Iterable[Request]:
        with open("sorted_teams.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            link = item['Link_to_team'].replace("startseite", "kader") + '/plus/0/galerie/0?saison_id='
            country = item['Country_Name']
            for year in range(self.years_start, self.years_end):
                url = f"https://www.transfermarkt.world{link}{year}"
                yield scrapy.Request(url, callback=self.parse, meta={'saison_id': year, 'country': country})

    def parse(self, response):
        year = response.meta['saison_id']
        country = response.meta['country']
        TeamId = response.url.split("/")[-5]

        AverageAge = response.xpath('.//tfoot/tr/td[@class="zentriert"]/text()').get()

        TeamCost = response.xpath('.//tfoot/tr/td[@class="rechts"][2]/text()').get()

        TeamSize = 0


        PlayerIDS = []
        legioners = 0

        for row in response.xpath('//tr[@class="odd"] | //tr[@class="even"]'):
            TeamSize += 1

            PlayerId = row.xpath('.//td[@class="posrela"]/table[@class="inline-table"]//a/@href').get()
            if PlayerId and "verein" not in PlayerId:
                PlayerId = PlayerId.strip().split("/")[-1]
                PlayerIDS.append(PlayerId)

            country_names = row.xpath('.//td[@class="zentriert"]/img/@title').getall()

            if country_names and ((len(country_names) == 1 and country not in country_names) or len(country_names) != 1)  :
                legioners += 1

        if TeamSize != len(PlayerIDS):
            self.logger.warning("PlayerLink not found for row.")

        yield {
            'TeamID ': TeamId,
            'Year': year,
            'TeamCost': TeamCost,
            'AverageAge': AverageAge,
            'Legioners': legioners,
            'TeamSize': TeamSize,
            'PlayerIDS': PlayerIDS
        }





