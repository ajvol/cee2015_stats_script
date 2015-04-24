# -*- coding: utf-8 -*-

#import pwb #only needed if you haven't installed the framework as side-package
#import pywikibot

import urllib2
import urllib
import json
import re
import pywikibot
import unicodedata
import sys
import codecs
from time import gmtime, strftime

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

site = pywikibot.Site('en','wikipedia')
repo = site.data_repository() 

#https://meta.wikimedia.org/w/index.php?title=Wikimedia_CEE_Spring_2015/Structure/Latvia

#http://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles=Venko%20Markovski&props=labels|sitelinks

#http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2015/Structure/Latvia&continue=


langs = ['az', 'ba', 'be', 'be-tarask', 'bg', 'bs', 'ce', 'cs', 'cv', 'de', 'el', 'et', 'hr', 'hu', 'hy', 'ka', 'kk', 'lt', 'lv', 'mk', 'os', 'pl', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'tr', 'uk']

lang_names = {'az':u'Azerbaijani - azərbaycan dili', 'ba':u'Bashkir - башҡорт теле', 'be':u'Belarusian - беларуская мова', 'be-tarask':u'Belarusian (Taraškievica) - беларуская мова (тарашкевіца)', 'bg':u'Bulgarian - български език', 'bs':u'Bosnian - bosanski jezik', 'ce':u'Chechen - нохчийн мотт', 'crh':u'Crimean Tatar - Къырым Татар', 'cs':u'Czech - čeština', 'cv':u'Chuvash - чӑваш чӗлхи', 'de':'German - Deutsche', 'el':u'Greek - ελληνικά', 'et':u'Estonian - eesti', 'hr':u'Croatian - hrvatski jezik', 'hu':u'Hungarian - magyar', 'hy':u'Armenian - Հայերեն', 'ka':u'Georgian - ქართული', 'kk':u'Kazakh - қазақ тілі', 'lt':u'Lithuanian - lietuvių kalba', 'lv':u'Latvian - latviešu valoda', 'mk':u'Macedonian - македонски јазик', 'os':u'Ossetian - ирон æвзаг', 'pl':u'Polish - polszczyzna', 'ro':u'Romanian - limba română', 'ru':u'Russian - русский язык', 'rue':u'Rusyn - 	русин', 'sk':u'Slovak - slovenčina', 'sl':u'Slovene - slovenščina', 'sq':u'Albanian - Shqip', 'sr':u'Serbian - српски језик', 'tr':u'Turkish - Türkçe', 'uk':u'Ukrainian - українська мова'}

countries = ['Albania', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Czech Republic', 'Cyprus', 'Estonia', 'Georgia', 'Greece', 'Hungary', 'Kazakhstan', 'Latvia', 'Lithuania', 'Macedonia', 'Moldova', 'Montenegro', 'Poland', 'Romania', 'Russia', 'Serbia', 'Slovakia', 'Slovenia', 'Turkey', 'Ukraine']


countries = ['Bulgaria','Bosnia and Herzegovina']
countries = ['Bulgaria']


for country in countries:
	print 'Auto generated at '+ strftime("%Y-%m-%d %H:%M:%S", gmtime())
	print u'== '+country+ u' =='

	print u'{| class="wikitable"'
	print u'|-'

	print u'! {{H:title|English article|en}}'
	print u'! wikidata'
	for key in sorted(langs):
		print (u'! {{H:title|'+lang_names[key]+u'|'+key+u'}}')

	try:
		co_list_req = urllib2.Request("http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2015/Structure/"+urllib.quote(country)+"&continue=")
		co_list_resp = urllib2.build_opener().open(co_list_req).read()
		co_list_json = json.loads(co_list_resp)
		#print "http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2015/Structure/"+country+"&continue="

	for itm in co_list_json["query"]["pages"]:
		wiki_text=co_list_json["query"]["pages"][itm]["revisions"][0]["*"]
	except:
		print '|}'
		continue

	for m in re.finditer(ur"\# *\[\[\:(.+?)\:(.+?)\|(.+?)\]\].*", wiki_text):
		try:
			l=m.group(1).strip()
			art=m.group(2).strip()
			#print l+':'+art

			item_req = urllib2.Request("http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&sites="+l+"wiki&titles="+urllib.quote(art.encode('utf-8'))+"&props=labels|sitelinks")
			item_resp = urllib2.build_opener().open(item_req).read()
			item_json = json.loads(item_resp)		

			item_label_dict = {}
			item_link_dict = {}

			for la in langs:
				item_label_dict[la] = ''
				item_link_dict[la] = ''

			for q in item_json["entities"]:
				if q == '-1':
					continue

				for item_label in item_json["entities"][q]["labels"]:
					item_label_lang = item_json["entities"][q]["labels"][item_label]["language"]
					item_label_value = item_json["entities"][q]["labels"][item_label]["value"]
				
					if item_label_lang in langs or item_label_lang=='en':
						item_label_dict[item_label_lang] = item_label_value

				for item_link in item_json["entities"][q]["sitelinks"]:
					item_link_lang = item_json["entities"][q]["sitelinks"][item_link]["site"]
					item_link_lang = item_link_lang.replace('wiki','')
					item_link_lang = item_link_lang.replace('be_x_old','be-tarask')
					item_link_value = item_json["entities"][q]["sitelinks"][item_link]["title"]
				
					if item_link_lang in langs or item_link_lang=='en':
						item_link_dict[item_link_lang] = item_link_value


			print u'|-'

			if 'en' not in item_label_dict or item_label_dict['en']=='':
				print u'| '+art
			else:
				print u'| style="background:#98FB98"| ' + u'[[:en:'+ item_link_dict['en'] + u'|'+item_label_dict['en']+u']]'

			if q=='-1':
				print u'| '
			else:
				print u'| style="background:#98FB98"| ' + u'[[:d:'+q+u'|'+q+u']]'
		

			for key in sorted(item_label_dict):
				if key != 'en':
					if item_link_dict[key]=='':
						print u'| '
					else:
						print u'| style="background:#98FB98"|[[:'+key.replace('be-tarask','be-x-old')+u':'+ item_link_dict[key] + u'|*****]]'
		except:
			error=1
	print '|}'

