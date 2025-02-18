from typing import Iterable
import scrapy
import json
from scrapy import Request


class NationalKaderSpider(scrapy.Spider):
    name = 'national_kader_spider'
    start_urls = ['https://www.transfermarkt.world']
    years_start = 2014 #inclusive
    years_end = 2025 #exclusive
    seen_team_ids = set()

    def start_requests(self) -> Iterable[Request]:
        with open("sorted_national_teams.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            link = item['Link_to_team'].replace("startseite", "kader") + '/plus/0/galerie/0?saison_id='
            id = item['NationalTeamID']
            for year in range(self.years_start, self.years_end):
                url = f"https://www.transfermarkt.world{link}{year}"
                yield scrapy.Request(url, callback=self.parse, meta={'saison_id': year, 'id': id})

    def parse(self, response):
        year = response.meta['saison_id']
        id = response.meta['id']

        TeamSize = 0
        PlayerIDS = []

        for row in response.xpath('//tr[@class="odd"] | //tr[@class="even"]'):
            TeamSize += 1

            PlayerId = row.xpath('.//td/table[@class="inline-table"]//a/@href').get()
            if PlayerId and "verein" not in PlayerId:
                PlayerId = PlayerId.strip().split("/")[-1]
                PlayerIDS.append(PlayerId)


        if TeamSize != len(PlayerIDS):
            self.logger.warning("PlayerLink not found for row.")

        yield {
            'TeamID ': id,
            'Year': year,
            'PlayerIDS': PlayerIDS
        }





