from typing import Iterable
import scrapy
from scrapy import Request


class NationalTeamsSpider(scrapy.Spider):
    name = 'national_teams'
    start_urls = ['https://www.transfermarkt.world/statistik/weltrangliste']
    pages_count = 9
    seen_team_ids = set()

    def start_requests(self) -> Iterable[Request]:
        for page in range(1, 1 + self.pages_count):
            url = f'https://www.transfermarkt.world/statistik/weltrangliste?page={page}'
            yield scrapy.Request(url, callback=self.parse, meta={'page': page})

    def parse(self, response):
        page_number = response.meta['page']
        teams = []

        for row in response.xpath('//tr[@class="odd"] | //tr[@class="even"]'):
            team_name = row.xpath('.//td[@class="hauptlink"]/a/text()').get().strip()
            link_to_team = row.xpath('.//td[@class="hauptlink"]/a/@href').get().strip()
            team_id = link_to_team.split("/")[-1]

            if team_id not in self.seen_team_ids:
                self.seen_team_ids.add(team_id)
                teams.append({
                    'NationalTeamID': team_id,
                    'NationalTeamName': team_name,
                    'Link_to_team': link_to_team,
                    'Page': page_number,
                })

        for team in teams:
            yield team
