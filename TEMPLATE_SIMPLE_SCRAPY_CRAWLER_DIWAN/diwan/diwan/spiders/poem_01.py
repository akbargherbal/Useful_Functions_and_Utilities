import scrapy

class PoemSpider(scrapy.Spider):
    name = 'poem_01'
    allowed_domains = ['aldiwan.net']
    low, high = 25, 10000
    start_urls = [f'https://www.aldiwan.net/poem{i}.html' for i in range(low, high)]

    def parse(self, response):
        xpath_age = '//div[@class="m-section-2 row"]//a[contains(@href, "poet")][1]//text()'
        xpath_poet = '//div[@class="m-section-2 row"]//a[contains(@href, "poet")][2]//text()'
        xpath_title = '//div[@class="m-section-2 row"]//h2[@class="h3"]/text()'
        xpath_no_verses = '//section[@class="container m-section-1"]//div[@class="s-menu1"]//p[contains(text(), "عدد الابيات")]//text()'
        xpath_verses = '//div[@class="s-menu1"][1]//div[@id="poem_content"]//h3//text()'
        xpath_no_poems = '//div[@class="s-menu1"]//div//div//p[contains(text(), "قصيدة")]/../p[1]//text()'
        xpath_poem_tags = '(//div[contains(text(), "نبذة عن القصيدة")]/../div)[last()]//div//text()'

        age = response.xpath(xpath_age).getall()
        poet = response.xpath(xpath_poet).getall()

        title = response.xpath(xpath_title).getall()
        title = ' '.join(title).strip()

        verses = response.xpath(xpath_verses).getall()
        verses = [i.strip() for i in verses if i.isspace()==False]

        no_verses = response.xpath(xpath_no_verses).getall()
        no_poems = response.xpath(xpath_no_poems).getall()

        poem_tags = response.xpath(xpath_poem_tags).getall()
        poem_tags = [i.strip() for i in poem_tags if i.isspace()==False]

        yield {
            'AGE':age,
            'POET': poet,
            'TITLE': title,
            'VERSES': verses,
            'NO_VERSES': no_verses,
            'NO_POEMS': no_poems,
            'POEM_TAGS': poem_tags,
            'POEM_URL': response.url
        }
