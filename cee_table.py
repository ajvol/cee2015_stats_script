#!/usr/bin/python
# -*- coding: utf-8 -*-
# https://meta.wikimedia.org/w/index.php?title=Wikimedia_CEE_Spring_2015

import traceback
import urllib2
import json
import re
import unicodedata
import sys
import codecs
from time import gmtime, strftime
from datetime import datetime
import requests


def savePage(title, content):
    user = 'Botik'
    passw = urllib2.quote(getPasswd())
    baseurl = 'https://meta.wikimedia.org/w/'
    summary = 'auto update'

    # Login request
    payload = {'action': 'query', 'format': 'json', 'utf8': '', 'meta': 'tokens', 'type': 'login'}
    r1 = requests.post(baseurl + 'api.php', data=payload)

    # login confirm
    login_token = r1.json()['query']['tokens']['logintoken']
    payload = {'action': 'login', 'format': 'json', 'utf8': '', 'lgname': user, 'lgpassword': passw, 'lgtoken': login_token}
    r2 = requests.post(baseurl + 'api.php', data=payload, cookies=r1.cookies)

    # get edit token
    payload = {'action': 'query', 'meta': 'tokens', 'format': 'json', 'continue': ''}
    r3 = requests.post(baseurl + 'api.php', data=payload, cookies=r2.cookies)

    edit_token = r3.json()['query']['tokens']['csrftoken']
    edit_cookie = r2.cookies.copy()
    edit_cookie.update(r3.cookies)

    # save action
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    payload = {'format': 'json', 'assert': 'user', 'action': 'edit', 'title': title, 'summary': summary,
               'text': content, 'token': edit_token}
    r4 = requests.post(baseurl + 'api.php', data=payload, headers=headers, cookies=edit_cookie)

    print(r4.text)


def getFirstEdit(server, title):
    timestamp = ''
    if server + ':' + title in cache:
        timestamp = cache[server + ':' + title]
    else:
        co_list_req = urllib2.Request("http://" + server + ".wikipedia.org/w/api.php?format=json&action=query&prop=revisions&titles=" + urllib2.quote(
            title.encode('utf-8')) + "&rvlimit=1&rvprop=timestamp&rvdir=newer&continue=")
        co_list_resp = urllib2.build_opener().open(co_list_req).read()
        co_list_json = json.loads(co_list_resp)

        for itm in co_list_json["query"]["pages"]:
            timestamp = co_list_json["query"]["pages"][itm]["revisions"][0]["timestamp"]
        cache[server + ':' + title] = timestamp
    if timestamp == '':
        timestamp = '2000-01-01T00:00:01Z'

    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


def getPasswd():
    try:
        f = open('passwd.txt', 'r')
        p = f.read().rstrip()
        f.close()
        return p
    except:
        print('passwd load error')


def getLastEdit(server, title):
    timestamp = ''
    co_list_req = urllib2.Request("http://" + server + ".wikipedia.org/w/api.php?format=json&action=query&prop=revisions&titles=" + urllib2.quote(
        title.encode('utf-8')) + "&rvlimit=1&rvprop=timestamp&rvdir=older&continue=")
    co_list_resp = urllib2.build_opener().open(co_list_req).read()
    co_list_json = json.loads(co_list_resp)

    for itm in co_list_json["query"]["pages"]:
        timestamp = co_list_json["query"]["pages"][itm]["revisions"][0]["timestamp"]

    if timestamp == '':
        timestamp = '2000-01-01T00:00:01Z'

    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


def ResolveRedirects(server, title):
    # http://lt.wikipedia.org/w/api.php?action=query&titles=Riga&redirects

    try:
        if 'r:' + server + ':' + title in cache:
            return cache['r:' + server + ':' + title]

        co_list_req = urllib2.Request("http://" + server + ".wikipedia.org/w/api.php?format=json&action=query&titles=" + urllib2.quote(
            title.encode('utf-8')) + "&redirects&continue=")
        co_list_resp = urllib2.build_opener().open(co_list_req).read()
        co_list_json = json.loads(co_list_resp)

        if 'redirects' in co_list_json["query"]:
            cache['r:' + server + ':' + title] = co_list_json["query"]["redirects"][0]["to"]
            return co_list_json["query"]["redirects"][0]["to"]
        else:
            cache['r:' + server + ':' + title] = title
            return title
    except Exception as e:
        print("".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))


def PublishStats():
    max_line = 80.0
    t = u''
    t = t + u'{{Notice|This page is updated daily by robot around midnight UTC}}' + '\n'
    t = t + u'{{Notice|Auto generated at ' + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' UTC}}' + '\n'

    t += u":''What could be more stupid than assessing contribution to Wikipedia by counting number of created articles? Only the automatic calculation of these figures.''\n"

    t += u'=== New articles by countries ===\n'
    t += u'{|\n'
    s2max = max(stats_by_country.values())
    point = 1.0 * max_line / s2max
    if point > 1:
        point = 1
    # for co in sorted(stats_by_country):
    for co in sorted(stats_by_country.keys(), lambda x, y: stats_by_country[y] - stats_by_country[x]):
        rep = int(round(point * stats_by_country[co]))
        if stats_by_country[co] > 0 and rep == 0:
            rep = 1
        t += u'|-\n'
        t += u'| ' + co + ' || ' + str(stats_by_country[co]) + ' || ' + (u'▒' * rep) + '\n'
    t += u'|}\n'

    t += u'=== New articles by languages ===\n'
    t += u'{|\n'
    s3max = max(stats_by_lang.values())
    point = 1.0 * max_line / s3max
    if point > 1:
        point = 1
    # for la in sorted(stats_by_lang):
    for la in sorted(stats_by_lang.keys(), lambda x, y: stats_by_lang[y] - stats_by_lang[x]):
        rep = int(round(point * stats_by_lang[la]))
        if stats_by_lang[la] > 0 and rep == 0:
            rep = 1
        t += u'|-\n'
        t += u'| ' + '{{H:title|' + lang_names[la] + u'|' + la.replace(u'be-tarask', u'be-t') + u'}}' + ' || ' + str(
            stats_by_lang[la]) + ' || ' + (u'▒' * rep) + '\n'
    t += u'|}\n'

    t += u'=== New articles timeline ===\n'
    for i, date in enumerate(sorted(stats_by_date, reverse=True)):
        itm = date.strftime("%Y-%m-%d %H:%M:%S")
        itm += ' [[:w:'+stats_by_date[date]+']]'
        t += u'* '+ itm+'\n'
        if i>=1000:
            break

    if debug == 0:
        savePage('Wikimedia_CEE_Spring_2016/Structure/Statistics', t)
    else:
        savePage('User:Botik/Stats', t)


try:
    f = open('./cee_cache.txt', 'r')
    cache = json.load(f)
    f.close()
except:
    cache = {}
    print('cache load error')

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

langs = ['az', 'be', 'be-tarask', 'bg', 'bs', 'cs', 'de', 'el', 'et', 'eo', 'hr', 'hu', 'hy', 'ka', 'lt',
         'lv', 'mk', 'pl', 'ro', 'ru', 'sk', 'sq', 'sr', 'uk', 'sh']
lang_names = {'sh': 'Serbo-Croatian - srpskohrvatski jezik', 'eo': u'Esperanto', 'az': u'Azerbaijani - azərbaycan dili',
              'ba': u'Bashkir - башҡорт теле', 'be': u'Belarusian - беларуская мова',
              'be-tarask': u'Belarusian (Taraškievica) - беларуская мова (тарашкевіца)',
              'bg': u'Bulgarian - български език', 'bs': u'Bosnian - bosanski jezik', 'ce': u'Chechen - нохчийн мотт',
              'crh': u'Crimean Tatar - Къырым Татар', 'cs': u'Czech - čeština', 'cv': u'Chuvash - чӑваш чӗлхи',
              'de': 'German - Deutsche', 'el': u'Greek - ελληνικά', 'et': u'Estonian - eesti',
              'hr': u'Croatian - hrvatski jezik', 'hu': u'Hungarian - magyar', 'hy': u'Armenian - Հայերեն',
              'ka': u'Georgian - ქართული', 'kk': u'Kazakh - қазақ тілі', 'lt': u'Lithuanian - lietuvių kalba',
              'lv': u'Latvian - latviešu valoda', 'mk': u'Macedonian - македонски јазик',
              'os': u'Ossetian - ирон æвзаг', 'pl': u'Polish - polszczyzna', 'ro': u'Romanian - limba română',
              'ru': u'Russian - русский язык', 'rue': u'Rusyn - 	русин', 'sk': u'Slovak - slovenčina',
              'sl': u'Slovene - slovenščina', 'sq': u'Albanian - Shqip', 'sr': u'Serbian - српски језик',
              'tr': u'Turkish - Türkçe', 'tt': u'Tatar - татар теле', 'uk': u'Ukrainian - українська мова'}

debug = 0

objects = {
    'Table': ['Albania', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia',
              'Czech Republic', 'Estonia', 'Georgia', 'Esperantujo',
              'Greece', 'Hungary', 'Latvia', 'Lithuania', 'Macedonia', 'Moldova', 'Poland', 'Romania', 'Russia',
              'Republika Srpska', 'Serbia',
              'Slovakia', 'Ukraine']}

if debug == 1:
    objects = {'Table': ['Serbia']}

stats_orig_list = {}
stats_by_country = {}
stats_by_lang = {}
stats_by_date = {}

for obj in sorted(objects):
    for country in sorted(objects[obj]):
        stats_orig_list[country] = 0
        stats_by_country[country] = 0
for lang in langs:
    stats_by_lang[lang] = 0

for obj in sorted(objects):

    for country in sorted(objects[obj]):
        q_list = list()

        print('+++++++++++' + country)

        try:
            co_list_req = urllib2.Request(
                "http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2016/Structure/" + urllib2.quote(
                    country) + "&continue=")
            co_list_resp = urllib2.build_opener().open(co_list_req).read()
            co_list_json = json.loads(co_list_resp)
            # print "http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2015/Structure/"+country+"&continue="

            for itm in co_list_json["query"]["pages"]:
                wiki_text = co_list_json["query"]["pages"][itm]["revisions"][0]["*"]
        except Exception as e:
            print("".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))
            continue

        qs = []
        mat = ''
        for line in wiki_text.split('\n'):
            # {{#invoke:WikimediaCEETable|table|Q948201|Q834689}}
            match = re.search(ur'\{\{\#invoke\:WikimediaCEETable\|table\|(.*)\}\}', line, re.IGNORECASE)
            if match is not None:
                mat = match.group(1).strip()
                qs += mat.split('|')

        for q in qs:
            print (q)

            r_url = "http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids=" + q + "&props=labels|sitelinks"

            item_req = urllib2.Request(r_url)
            item_resp = urllib2.build_opener().open(item_req).read()
            item_json = json.loads(item_resp)

            item_label_dict = {}
            item_link_dict = {}

            try:

                for la in langs:
                    item_label_dict[la] = ''
                    item_link_dict[la] = ''

                for q2 in item_json["entities"]:
                    if q2 == '-1':
                        continue
                    q = q2

                if q in q_list:
                    continue
                elif q != '':
                    q_list.append(q)

                for item_label in item_json["entities"][q]["labels"]:
                    item_label_lang = item_json["entities"][q]["labels"][item_label]["language"]
                    item_label_value = item_json["entities"][q]["labels"][item_label]["value"]

                    if item_label_lang in langs or item_label_lang == 'en':
                        item_label_dict[item_label_lang] = item_label_value

                if "sitelinks" in item_json["entities"][q]:
                    for item_link in item_json["entities"][q]["sitelinks"]:
                        item_link_lang = item_json["entities"][q]["sitelinks"][item_link]["site"]
                        item_link_lang = item_link_lang.replace('wiki', '')
                        item_link_lang = item_link_lang.replace('be_x_old', 'be-tarask')
                        item_link_value = item_json["entities"][q]["sitelinks"][item_link]["title"]

                        if item_link_lang in langs or item_link_lang == 'en':
                            item_link_dict[item_link_lang] = item_link_value

                if q == '-1':
                    stats_orig_list[country] += 1
                else:
                    stats_orig_list[country] += 1

                for key in sorted(item_label_dict):
                    if (key != 'en') and (len(item_link_dict[key]) > 1):
                        fe = getFirstEdit(key, item_link_dict[key])

                        if fe >= datetime.strptime('2016-03-21', "%Y-%m-%d"):
                            stats_by_country[country] += 1
                            stats_by_lang[key] += 1
                            stats_by_date[fe] = key+':'+item_link_dict[key]
            except Exception as e:
                print("".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])))

print(stats_orig_list)
print(stats_by_country)
print(stats_by_lang)
print(stats_by_date)

PublishStats()

try:
    f = open('./cee_cache.txt', 'w')
    json.dump(cache, f)
    f.close()
except:
    print('Failed to save cache')
