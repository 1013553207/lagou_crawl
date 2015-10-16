#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json

import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request, FormRequest, Response



class LagouItem(scrapy.Item):
    job = scrapy.Field()


class LagouSipder(CrawlSpider) :
    name = "lagou"
    allowed_domains = ["www.lagou.com"]
    start_urls = [
        "http://www.lagou.com/"
    ]
    json_url = "http://www.lagou.com/jobs/positionAjax.json?px=default"
    rules = (
        Rule(LinkExtractor(allow = ('/zhaopin/\w+.*', ), allow_domains="www.lagou.com", ), callback = 'parse_zhaopin', follow = True),
        # Rule(LinkExtractor(allow = ('/jobs/\d+\.html', )), callback = 'parse_jobs', follow = True),
    )

    def parse_jobs(self, response):
        sel = Selector(response)
        for desc in sel.xpath("//dd[@class='job_bt']/p/text()").extract():
            if isinstance(desc, unicode):
                print desc

    def parse_zhaopin(self, response):
        sel = Selector(response)
        regex_rule = r'http://www.lagou.com/zhaopin/(.*?)/'
        result = re.match(regex_rule, response.url)
        formdata = {'first' : 'false', 'pg': str(1)}
        if result:
            formdata['kd'] = result.group(1)

        request = FormRequest(url=self.json_url,
                           method='POST',
                           formdata=formdata,
                           callback=self.parse_first_json)
        request.meta['kd'] = formdata['kd']
        return request
    
    def parse_first_json(self, response):
        result = json.loads(response.body, encoding='UTF-8')
        if not result['success']:
            raise StopIteration()
        pagesize = int(result['content']['totalPageCount'])
        nextpage = int(result.get('pageNo', 0)) + 1
        for i in result['content']['result']:
            lagou_item = LagouItem()
            lagou_item['job'] = i
            yield lagou_item
        
        for i in xrange(nextpage, pagesize+1):
            formdata = {'kd': response.meta['kd'],
                        'first' : 'false',
                        'pg': str(i)
                        }
            yield FormRequest(url=self.json_url,
                           method='POST',
                           formdata=formdata,
                           callback=self.parse_second_json)
    
    def parse_second_json(self, response):
        result = json.loads(response.body, encoding='UTF-8')
        if not result['success']:
            raise StopIteration()
        for i in result['content']['result']:
            lagou_item = LagouItem()
            lagou_item['job'] = i
            yield lagou_item



