from typing import Iterable
import scrapy
import json
from scrapy import Request


class TransferBalanceSpider(scrapy.Spider):
    name = 'transfer_balance'
    start_urls = ['https://www.transfermarkt.world']
    years_start = 2014  # inclusive
    years_end = 2025  # exclusive
    seen_team_ids = set()

    def start_requests(self) -> Iterable[Request]:
        with open("sorted_teams.json", 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            link = item['Link_to_team'].replace("startseite", "transfers") + '/plus/?saison_id='
            country = item['Country_Name']
            TeamId = item['TeamID']
            for year in range(self.years_start, self.years_end):
                url = f"https://www.transfermarkt.world{link}{year}&pos=&detailpos=&w_s="
                yield scrapy.Request(url, callback=self.parse, meta={'saison_id': year, 'TeamID': TeamId})

    def parse(self, response):
        year = response.meta['saison_id']
        TeamId = response.meta['TeamID']

        transferBalanceValue = response.xpath(
            './/div[@class="box transfer-record"]/table/tfoot/tr/td[contains(@class, "rechts transfer-record__total")]/text()').get().strip()

        transferBalanceMer = response.xpath(
            './/div[@class="box transfer-record"]/table/tfoot/tr/td[contains(@class, "rechts transfer-record__total")]/span[@class="abloeseZusatz"]/text()').get()

        yield {
            'TeamID ': TeamId,
            'Year': year,
            'TransferBalanceValue': transferBalanceValue,
            'TransferBalanceMer': transferBalanceMer
        }
