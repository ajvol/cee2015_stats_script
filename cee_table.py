# -*- coding: utf-8 -*-
#https://meta.wikimedia.org/w/index.php?title=Wikimedia_CEE_Spring_2015

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
	user    = 'Botik'
	passw   = urllib2.quote('fantom%botik')
	baseurl = 'https://meta.wikimedia.org/w/'
	params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)
	summary='auto update'
	 
	# Login request
	r1 = requests.post(baseurl+'api.php'+params)
	token = r1.json()['login']['token']

	#login confirm
	params2 = params+'&lgtoken=%s'% token
	r2 = requests.post(baseurl+'api.php'+params2,cookies=r1.cookies)
	
	#get timestamp
	timestamp=''
	r3 =  requests.get(baseurl+'api.php'+'?format=json&action=query&prop=revisions&titles='+title+'&rvprop=timestamp&continue=', cookies=r2.cookies)
	ts_json = json.loads(r3.text)
	try:
		for itm in ts_json["query"]["pages"]:
			timestamp=ts_json["query"]["pages"][itm]["revisions"][0]["timestamp"]	
	except:
		timestamp=''

	#get token
	r4 = requests.get(baseurl+'api.php'+'?format=json&action=query&meta=tokens&continue=', cookies=r3.cookies)
	token2 = r4.json()['query']['tokens']['csrftoken']
	print(token2)

	# save action
	headers = {'content-type': 'application/x-www-form-urlencoded'}
	payload = {'format': 'json', 'action': 'edit', 'title': title, 'summary': summary, 'text': content, 'basetimestamp': timestamp, 'token': token2}
	r5 = requests.post(baseurl+'api.php', data=payload, headers=headers, cookies=r4.cookies)
	print (r5.text)

def getFirstEdit(server, title):
	timestamp=''
	if server+':'+title in cache:
		timestamp=cache[server+':'+title]
	else:
		co_list_req = urllib2.Request("http://"+server.replace('be-tarask','be-x-old')+".wikipedia.org/w/api.php?format=json&action=query&prop=revisions&titles="+urllib2.quote(title.encode('utf-8'))+"&rvlimit=1&rvprop=timestamp&rvdir=newer&continue=")
		co_list_resp = urllib2.build_opener().open(co_list_req).read()
		co_list_json = json.loads(co_list_resp)
	
		for itm in co_list_json["query"]["pages"]:
			timestamp=co_list_json["query"]["pages"][itm]["revisions"][0]["timestamp"]
		cache[server+':'+title]=timestamp
	if timestamp=='':
		timestamp='2000-01-01T00:00:01Z'
		
	return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

def getLastEdit(server, title):
	timestamp=''
	co_list_req = urllib2.Request("http://"+server.replace('be-tarask','be-x-old')+".wikipedia.org/w/api.php?format=json&action=query&prop=revisions&titles="+urllib2.quote(title.encode('utf-8'))+"&rvlimit=1&rvprop=timestamp&rvdir=older&continue=")
	co_list_resp = urllib2.build_opener().open(co_list_req).read()
	co_list_json = json.loads(co_list_resp)
	
	for itm in co_list_json["query"]["pages"]:
		timestamp=co_list_json["query"]["pages"][itm]["revisions"][0]["timestamp"]

	if timestamp=='':
		timestamp='2000-01-01T00:00:01Z'
		
	return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

f = open('./cee_cache.txt', 'r')
cache = json.load(f)
f.close()

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)


langs = ['az', 'ba', 'be', 'be-tarask', 'bg', 'bs', 'ce', 'cs', 'cv', 'de', 'el', 'et', 'hr', 'hu', 'hy', 'ka', 'kk', 'lt', 'lv', 'mk', 'os', 'pl', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'tr', 'uk']

lang_names = {'az':u'Azerbaijani - azərbaycan dili', 'ba':u'Bashkir - башҡорт теле', 'be':u'Belarusian - беларуская мова', 'be-tarask':u'Belarusian (Taraškievica) - беларуская мова (тарашкевіца)', 'bg':u'Bulgarian - български език', 'bs':u'Bosnian - bosanski jezik', 'ce':u'Chechen - нохчийн мотт', 'crh':u'Crimean Tatar - Къырым Татар', 'cs':u'Czech - čeština', 'cv':u'Chuvash - чӑваш чӗлхи', 'de':'German - Deutsche', 'el':u'Greek - ελληνικά', 'et':u'Estonian - eesti', 'hr':u'Croatian - hrvatski jezik', 'hu':u'Hungarian - magyar', 'hy':u'Armenian - Հայերեն', 'ka':u'Georgian - ქართული', 'kk':u'Kazakh - қазақ тілі', 'lt':u'Lithuanian - lietuvių kalba', 'lv':u'Latvian - latviešu valoda', 'mk':u'Macedonian - македонски јазик', 'os':u'Ossetian - ирон æвзаг', 'pl':u'Polish - polszczyzna', 'ro':u'Romanian - limba română', 'ru':u'Russian - русский язык', 'rue':u'Rusyn - 	русин', 'sk':u'Slovak - slovenčina', 'sl':u'Slovene - slovenščina', 'sq':u'Albanian - Shqip', 'sr':u'Serbian - српски језик', 'tr':u'Turkish - Türkçe', 'uk':u'Ukrainian - українська мова'}

#countries = ['Bulgaria','Bosnia and Herzegovina']
#countries = ['Albania']


objects = {'Table': ['Albania', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Czech Republic', 'Cyprus'], 'Table2': ['Estonia', 'Georgia', 'Greece', 'Hungary', 'Kazakhstan', 'Latvia'], 'Table3': ['Lithuania', 'Macedonia', 'Moldova', 'Montenegro', 'Poland', 'Romania', 'Russia', 'Serbia', 'Slovakia', 'Slovenia', 'Turkey', 'Ukraine'] }

for obj in sorted(objects):
	print('=========='+obj)	

	txt=u''
	txt=txt+u'Auto generated at '+ strftime("%Y-%m-%d %H:%M:%S", gmtime())+' UTC' +'\n'

	txt=txt+'''
* [[Wikimedia CEE Spring 2015/Structure/Table]] (Albania - Armenia - Austria - Azerbaijan - Belarus - Bosnia and Herzegovina - Bulgaria - Croatia - Czech Republic - Cyprus)
* [[Wikimedia CEE Spring 2015/Structure/Table2]] (Estonia - Georgia - Greece - Hungary - Kazakhstan - Latvia)
* [[Wikimedia CEE Spring 2015/Structure/Table3]] (Lithuania - Macedonia - Moldova - Montenegro - Poland - Romania - Russia - Serbia - Slovakia - Slovenia - Turkey - Ukraine)

{| class="wikitable"
|-
! Color !! Meaning
|-
| style="background:#98FB98" | green || new articles created after CEE start (2015-03-20)
|-
| style="background:#ffc757" | orange || old articles, changed after CEE start
|-
| style="background:#FFFF00" | yellow || old unchanged articles
|}
'''
	for country in sorted(objects[obj]):
		print('+++++++++++'+country)		

		txt=txt+ u'== '+country+ u' =='+'\n'

		txt=txt+ u'{| class="wikitable"'+'\n'
		txt=txt+ u'|-'+'\n'

		txt=txt+ u'! {{H:title|English article|en}}'+'\n'
		txt=txt+ u'! wikidata'+'\n'
		for key in sorted(langs):
			txt=txt+ (u'! {{H:title|'+lang_names[key]+u'|'+key+u'}}') +'\n'

		try:
			co_list_req = urllib2.Request("http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2015/Structure/"+urllib2.quote(country)+"&continue=")
			co_list_resp = urllib2.build_opener().open(co_list_req).read()
			co_list_json = json.loads(co_list_resp)
			#print "http://meta.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=Wikimedia_CEE_Spring_2015/Structure/"+country+"&continue="

			for itm in co_list_json["query"]["pages"]:
				wiki_text=co_list_json["query"]["pages"][itm]["revisions"][0]["*"]
		except:
			txt=txt+ '|}'+'\n'
			continue

		for line in wiki_text.split('\n'):
			#print line
			l=''
			art=''
			q=''
			r_url = ''

			#<h3 style="color:#339966;">[[File:P art-green.png|30px]] '''a. Culture'''</h3>
			match = re.search(ur"<h3(.*)'''(.*?)'''</h3>", line)
			if match is not None:
				txt=txt+ u'|-'+'\n'
				txt=txt+ u'| colspan="'+str(len(langs)+2)+'" style="background:#dddddd" | '+ match.group(2).strip() +'\n'
				continue

			#=== [[File:P art-green.png|30px]] '''Culture''' ===
			match = re.search(ur"===(.*)png(.*)'''(.*?)'''", line)
			if match is not None:
				txt=txt+ u'|-'+'\n'
				txt=txt+ u'| colspan="'+str(len(langs)+2)+'" style="background:#dddddd" | '+ match.group(3).strip()+'\n'
				continue

			#=== General ===
			match = re.search(ur"=== (.*) ===", line)
			if match is not None:
				txt=txt+ u'|-'+'\n'
				txt=txt+ u'| colspan="'+str(len(langs)+2)+'" style="background:#dddddd" | '+ match.group(1).strip()+'\n'
				continue

			#==== Islands ====
			match = re.search(ur"====(.*)====", line)
			if match is not None:
				txt=txt+ u'|-'+'\n'
				txt=txt+ u'| colspan="'+str(len(langs)+2)+'" style="background:#dddddd" | '+ match.group(1).strip()+'\n'
				continue

			# [[d:Q2499614|Q2499614]]
			match = re.search(ur"\[\[\:?d\:Q(\d+?)\|Q(\d+?)\]\]", line, re.IGNORECASE)
			if match is not None:
				q = match.group(1).strip()
				q = 'Q'+q

			else:
				#  # [[:en:Theater of Armenia|'''Theater of Armenia''']]
				match = re.search(ur"\#(.*?)\[\[\:?(.{2,9}?)\:(.+?)\|(.+?)\]\]", line) 
				if match is not None and not (line[0]=='|' and country=='Estonia'):
					l=match.group(2).strip()
					art=match.group(3).strip()

				else:
					# ([[:hy:Հայկական թատրոն|hy]],...)
					match = re.search(ur"\(\[\[\:(.{2,9}?)\:(.+?)\|(.+?)\]\]", line) 
					if match is not None and not (line[0]=='|' and country=='Estonia'):
						l=match.group(1).strip()
						art=match.group(2).strip()
					else:
						# |[[w:en:Jakub Wujek Bible|Jakub Wujek Bible]]
						match = re.search(ur"\|(.*)\[\[\w?:en\:(.+?)\|(.+?)\]\]", line) 
						if match is not None and country=='Poland':
							l='en'
							art=match.group(2).strip()
						else:	
							# | [[File:Poland-orb.png|10px]][[w:pl:Grabarka (góra)|Grabarka (góra)]]
							match = re.search(ur"\|(.*)Poland-orb.png(.*)\[\[\w?:pl\:(.+?)\|(.+?)\]\]", line)
							if match is not None and country=='Poland':
								l='pl'
								art=match.group(3).strip()				

			if q!='':
				r_url = "http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids="+q+"&props=labels|sitelinks"
			elif q=='' and l!='':
				r_url = "http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&sites="+l+"wiki&titles="+urllib2.quote(art.encode('utf-8'))+"&props=labels|sitelinks"
			else:
				continue

			print (q+':'+l+':'+art)
		
			item_req = urllib2.Request(r_url)
			item_resp = urllib2.build_opener().open(item_req).read()
			item_json = json.loads(item_resp)		

			item_label_dict = {}
			item_link_dict = {}

			try:

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


				txt=txt+ u'|-'+'\n'

				if 'en' not in item_label_dict or item_label_dict['en']=='':
					if art <> '':
						txt=txt+ u'| '+art+'\n'
					else:
						inverse = [(value, key) for key, value in item_label_dict.items()]
						txt=txt+ u'| '+max(inverse)[0]+'\n'
				else:
					txt=txt+ u'| style="background:#fff8dc"| ' + u'[[:en:'+ item_link_dict['en'] + u'|'+item_label_dict['en']+u']]'+'\n'

				if q=='-1':
					txt=txt+ u'| '+'\n'
				else:
					txt=txt+ u'| style="background:#fff8dc"| ' + u'[[:d:'+q+u'|'+q+u']]'+'\n'
		

				for key in sorted(item_label_dict):
					if key != 'en':
						if item_link_dict[key]=='':
							txt=txt+ u'| '+'\n'
						else:
							fe = getFirstEdit(key, item_link_dict[key])

							if fe < datetime.strptime('2015-03-20', "%Y-%m-%d"):
								le = getLastEdit(key, item_link_dict[key])
								if le > datetime.strptime('2015-03-20', "%Y-%m-%d"):
									#orange
									txt=txt+ u'| style="background:#ffc757"|[[:'+key.replace('be-tarask','be-x-old')+u':'+ item_link_dict[key] + u'|***]]'+'\n'
								else:
									#yellow
									txt=txt+ u'| style="background:#FFFF00"|[[:'+key.replace('be-tarask','be-x-old')+u':'+ item_link_dict[key] + u'|***]]'+'\n'
							else:
								# green
								txt=txt+ u'| style="background:#98FB98"|[[:'+key.replace('be-tarask','be-x-old')+u':'+ item_link_dict[key] + u'|***]]'+'\n'
			except:
				print 'error'
		txt=txt+ '|}'+'\n'

	#savePage('Wikimedia_CEE_Spring_2015/Structure/'+obj, txt)
	savePage('User:Botik/'+obj, txt)

f = open('./cee_cache.txt', 'w')
json.dump(cache, f)
f.close()
