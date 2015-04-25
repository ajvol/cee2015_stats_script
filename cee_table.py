#!/usr/bin/python
# -*- coding: utf-8 -*-
#https://meta.wikimedia.org/w/index.php?title=Wikimedia_CEE_Spring_2015

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
	user    = 'Botik'
	passw   = urllib2.quote(getPasswd())
	baseurl = 'https://meta.wikimedia.org/w/'
	params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)
	summary='auto update'
	 
	# Login request
	r1 = requests.post(baseurl+'api.php'+params)
	login_token = r1.json()['login']['token']

	#login confirm
	params2 = params+'&lgtoken=%s'% login_token
	r2 = requests.post(baseurl+'api.php'+params2, cookies=r1.cookies)
	
	#get edit token
	r3 = requests.get(baseurl+'api.php'+'?format=json&action=query&meta=tokens&continue=', cookies=r2.cookies)
	edit_token = r3.json()['query']['tokens']['csrftoken']

	edit_cookie = r2.cookies.copy()
	edit_cookie.update(r3.cookies)

	# save action
	headers = {'content-type': 'application/x-www-form-urlencoded'}
	payload = {'format': 'json', 'assert': 'user', 'action': 'edit', 'title': title, 'summary': summary, 'text': content, 'token': edit_token}
	r4 = requests.post(baseurl+'api.php', data=payload, headers=headers, cookies=edit_cookie)
	print (r4.text)

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

def getPasswd():
	try:
		f = open('passwd.txt', 'r')
		p = f.read().rstrip() 
		f.close()
		return p
	except:
		print ('passwd load error')	

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

def ResolveRedirects(server, title):
	#http://lt.wikipedia.org/w/api.php?action=query&titles=Riga&redirects

	try:
		if 'r:'+server+':'+title in cache:
			return cache['r:'+server+':'+title]
		
		co_list_req = urllib2.Request("http://"+server.replace('be-tarask','be-x-old')+".wikipedia.org/w/api.php?format=json&action=query&titles="+urllib2.quote(title.encode('utf-8'))+"&redirects&continue=")
		co_list_resp = urllib2.build_opener().open(co_list_req).read()
		co_list_json = json.loads(co_list_resp)

		if 'redirects' in co_list_json["query"]:
			cache['r:'+server+':'+title]=co_list_json["query"]["redirects"][0]["to"]
			return co_list_json["query"]["redirects"][0]["to"]
		else:
			cache['r:'+server+':'+title]=title
			return title
	except Exception as e:
		print "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))

def PublishStats():
	max_line = 80.0
	t=u''
	t=t+u'{{Notice|This page is updated daily by robot around midnight UTC}}' +'\n'
	t=t+u'Auto generated at '+ strftime("%Y-%m-%d %H:%M:%S", gmtime())+' UTC' +'\n'

	t=t+'''
* [[Wikimedia CEE Spring 2015/Structure/Table]] (Albania, Armenia, Austria, Azerbaijan, Belarus)
* [[Wikimedia CEE Spring 2015/Structure/Table2]] (Bosnia and Herzegovina, Bulgaria, Croatia, Cyprus, Czech Republic)
* [[Wikimedia CEE Spring 2015/Structure/Table3]] (Estonia, Georgia, Greece, Hungary, Kazakhstan)
* [[Wikimedia CEE Spring 2015/Structure/Table4]] (Latvia, Lithuania, Macedonia, Moldova, Montenegro)
* [[Wikimedia CEE Spring 2015/Structure/Table5]] (Poland, Romania, Russia, Serbia)
* [[Wikimedia CEE Spring 2015/Structure/Table6]] (Slovakia, Slovenia, Turkey, Ukraine)
* [[Wikimedia CEE Spring 2015/Structure/Statistics]]
'''
	t += u'== Article lists statistics ==\n'
	t += u":''What could be more stupid than assessing contribution to Wikipedia by counting number of created articles? Only the automatic calculation of these figures.''\n"

	t += u'=== Articles in proposition lists by country ===\n'
	t += u'{|\n'
	s1max = max(stats_orig_list.values())
	point = 1.0 * max_line / s1max
	if point > 1:
		point = 1
#	for co in sorted(stats_orig_list):
	for co in sorted(stats_orig_list.keys(), lambda x,y:stats_orig_list[y]-stats_orig_list[x]):
		rep = int(round(point * stats_orig_list[co]))
		if stats_orig_list[co] > 0 and rep == 0:
			rep = 1
		t += u'|-\n'
		t += u'| '+co+' || '+str(stats_orig_list[co])+' || '+(u'▒' * rep) + '\n'
	t += u'|}\n'		

	t += u'=== New articles by countries ===\n'
	t += u'{|\n'
	s2max = max(stats_by_country.values())
	point = 1.0 * max_line / s2max
	if point > 1:
		point = 1
	#for co in sorted(stats_by_country):
	for co in sorted(stats_by_country.keys(), lambda x,y:stats_by_country[y]-stats_by_country[x]):
		rep = int(round(point * stats_by_country[co]))
		if stats_by_country[co] > 0 and rep == 0:
			rep = 1
		t += u'|-\n'
		t += u'| '+co+' || '+str(stats_by_country[co])+' || '+(u'▒' * rep) + '\n'
	t += u'|}\n'

	t += u'=== New articles by languages ===\n'
	t += u'{|\n'
	s3max = max(stats_by_lang.values())
	point = 1.0 * max_line / s3max
	if point > 1:
		point = 1
	#for la in sorted(stats_by_lang):
	for la in sorted(stats_by_lang.keys(), lambda x,y:stats_by_lang[y]-stats_by_lang[x]):
		rep = int(round(point * stats_by_lang[la]))
		if stats_by_lang[la] > 0 and rep == 0:
			rep = 1
		t += u'|-\n'
		t += u'| '+'{{H:title|'+lang_names[la]+u'|'+la.replace(u'be-tarask',u'be-t')+u'}}'+' || '+str(stats_by_lang[la])+' || '+(u'▒' * rep) + '\n'
	t += u'|}\n'

	if debug==0:
		savePage('Wikimedia_CEE_Spring_2015/Structure/Statistics', t)
	else:
		savePage('User:Botik/Stats', t)

try:
	f = open('/home/ajvol/pywikibot/forenames/cee_cache.txt', 'r')
	cache = json.load(f)
	f.close()
except:
	cache = {}
	print ('cache load error')

UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)


langs = ['az', 'ba', 'be', 'be-tarask', 'bg', 'bs', 'ce', 'cs', 'cv', 'de', 'el', 'et', 'hr', 'hu', 'hy', 'ka', 'kk', 'lt', 'lv', 'mk', 'os', 'pl', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'tr', 'tt', 'uk']
lang_names = {'az':u'Azerbaijani - azərbaycan dili', 'ba':u'Bashkir - башҡорт теле', 'be':u'Belarusian - беларуская мова', 'be-tarask':u'Belarusian (Taraškievica) - беларуская мова (тарашкевіца)', 'bg':u'Bulgarian - български език', 'bs':u'Bosnian - bosanski jezik', 'ce':u'Chechen - нохчийн мотт', 'crh':u'Crimean Tatar - Къырым Татар', 'cs':u'Czech - čeština', 'cv':u'Chuvash - чӑваш чӗлхи', 'de':'German - Deutsche', 'el':u'Greek - ελληνικά', 'et':u'Estonian - eesti', 'hr':u'Croatian - hrvatski jezik', 'hu':u'Hungarian - magyar', 'hy':u'Armenian - Հայերեն', 'ka':u'Georgian - ქართული', 'kk':u'Kazakh - қазақ тілі', 'lt':u'Lithuanian - lietuvių kalba', 'lv':u'Latvian - latviešu valoda', 'mk':u'Macedonian - македонски јазик', 'os':u'Ossetian - ирон æвзаг', 'pl':u'Polish - polszczyzna', 'ro':u'Romanian - limba română', 'ru':u'Russian - русский язык', 'rue':u'Rusyn - 	русин', 'sk':u'Slovak - slovenčina', 'sl':u'Slovene - slovenščina', 'sq':u'Albanian - Shqip', 'sr':u'Serbian - српски језик', 'tr':u'Turkish - Türkçe', 'tt':u'Tatar - татар теле', 'uk':u'Ukrainian - українська мова'}


debug=0

objects = {'Table': ['Albania', 'Armenia', 'Austria', 'Azerbaijan', 'Belarus'], 'Table2': ['Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic'], 'Table3': ['Estonia', 'Georgia', 'Greece', 'Hungary', 'Kazakhstan'], 'Table4': ['Latvia', 'Lithuania', 'Macedonia', 'Moldova', 'Montenegro'], 'Table5': ['Poland', 'Romania', 'Russia', 'Serbia'], 'Table6': ['Slovakia', 'Slovenia', 'Turkey', 'Ukraine'] }

if debug==1:
	objects = {'Table': ['Austria', 'Albania'] }

stats_orig_list = {}
stats_by_country = {}
stats_by_lang = {}

for obj in sorted(objects):
	for country in sorted(objects[obj]):
		stats_orig_list[country] = 0
		stats_by_country[country] = 0
for lang in langs:
	stats_by_lang[lang] = 0

for obj in sorted(objects):
	print('=========='+obj)	

	txt=u''
	txt=txt+u'{{Notice|This page is updated daily by robot around midnight UTC}}' +'\n'
	txt=txt+u'Auto generated at '+ strftime("%Y-%m-%d %H:%M:%S", gmtime())+' UTC' +'\n'

	txt=txt+'''
* [[Wikimedia CEE Spring 2015/Structure/Table]] (Albania, Armenia, Austria, Azerbaijan, Belarus)
* [[Wikimedia CEE Spring 2015/Structure/Table2]] (Bosnia and Herzegovina, Bulgaria, Croatia, Cyprus, Czech Republic)
* [[Wikimedia CEE Spring 2015/Structure/Table3]] (Estonia, Georgia, Greece, Hungary, Kazakhstan)
* [[Wikimedia CEE Spring 2015/Structure/Table4]] (Latvia, Lithuania, Macedonia, Moldova, Montenegro)
* [[Wikimedia CEE Spring 2015/Structure/Table5]] (Poland, Romania, Russia, Serbia)
* [[Wikimedia CEE Spring 2015/Structure/Table6]] (Slovakia, Slovenia, Turkey, Ukraine)
* [[Wikimedia CEE Spring 2015/Structure/Statistics]]

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
		q_list = list()
		
		print('+++++++++++'+country)		

		txt=txt+ u'== '+country+ u' =='+'\n'
		
		txt=txt+ u":''Source list: [[Wikimedia_CEE_Spring_2015/Structure/" + country + u"]]''"+'\n'

		txt=txt+ u'{| class="wikitable"'+'\n'
		txt=txt+ u'|-'+'\n'
	
		txt=txt+ u'! style="width:20em" | {{H:title|English article|en}}'+'\n'
		txt=txt+ u'! style="width:6em" | wikidata'+'\n'
		for key in sorted(langs):
			txt=txt+ u'! {{H:title|'+lang_names[key]+u'|'+key.replace(u'be-tarask',u'be-t')+u'}}' +u'\n'

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
			l_res=''
			art=''
			art_res=''
			q=''
			r_url = ''
			en_title=''

			line = re.sub(r'\[\[File:.*?\]\]', r'', line)
			line = re.sub(r'\[\[Image:.*?\]\]', r'', line)

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

			#  # [[:en:Theater of Armenia|'''Theater of Armenia''']]
			match = re.search(ur"^\#(.*?)\[\[\:?(.{2,9}?)\:(.+?)\|(.+?)\]\]", line) 
			if match is not None and not (line[0]=='|' and country=='Estonia') and not country=='Greece':
				l=match.group(2).strip()
				art=match.group(3).strip()
				if l=='en':
					en_title=art.replace('_',' ')

			else:
				# ([[:hy:Հայկական թատրոն|hy]],...)
				match = re.search(ur"\(\[\[\:(.{2,9}?)\:(.+?)\|(.+?)\]\]", line) 
				if match is not None and not (line[0]=='|' and country=='Estonia'):
					l=match.group(1).strip()
					art=match.group(2).strip()
					if l=='en':
						en_title=art.replace('_',' ')						
				else:
					# |[[w:en:Jakub Wujek Bible|Jakub Wujek Bible]]
					match = re.search(ur"\|(.*)\[\[\w?:en\:(.+?)\|(.+?)\]\]", line) 
					if match is not None and country=='Poland':
						l='en'
						art=match.group(2).strip()
						en_title=art.replace('_',' ')
					else:	
						# | [[File:Poland-orb.png|10px]][[w:pl:Grabarka (góra)|Grabarka (góra)]]
						match = re.search(ur"\|(.*)Poland-orb.png(.*)\[\[\w?:pl\:(.+?)\|(.+?)\]\]", line)
						if match is not None and country=='Poland':
							l='pl'
							art=match.group(3).strip()
						else:	
							# #[[:en:Theatre of ancient Greece]]
							match = re.search(ur"\#( )*\[\[\:?(.{2,9}?)\:(.+?)\]\]", line) 
							if match is not None:
								l=match.group(2).strip()
								art=match.group(3).strip()	
								if l=='en':
									en_title=art.replace('_',' ')										

			if en_title == '':
				match = re.search(ur"'''(.+?)'''", line) 
				if match is not None:
					en_title=match.group(1).strip()


			# reserve 
			# ([[:hy:Հայկական թատրոն|hy]],...)
			match = re.search(ur"\(\[\[\:(.{2,9}?)\:(.+?)\|(.+?)\]\]", line) 
			if match is not None and not (line[0]=='|' and country=='Estonia'):
				l_res=match.group(1).strip()
				art_res=match.group(2).strip()
									
			if q!='':
				r_url = "http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&ids="+q+"&props=labels|sitelinks"
			elif q=='' and l!='':
				art=ResolveRedirects(l, art)
				r_url = "http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&sites="+l+"wiki&titles="+urllib2.quote(art.encode('utf-8'))+"&props=labels|sitelinks"
			else:
				continue
	
			item_req = urllib2.Request(r_url)
			item_resp = urllib2.build_opener().open(item_req).read()
			item_json = json.loads(item_resp)		

			# we use reserve, if English article is absent
			if l_res!='' and ((not "entities" in item_json) or ('-1' in item_json["entities"])):
				art_res=ResolveRedirects(l_res, art_res)
				r_url = "http://www.wikidata.org/w/api.php?format=json&action=wbgetentities&sites="+l_res+"wiki&titles="+urllib2.quote(art_res.encode('utf-8'))+"&props=labels|sitelinks"
				item_req = urllib2.Request(r_url)
				item_resp = urllib2.build_opener().open(item_req).read()
				item_json = json.loads(item_resp)
				art = art_res
				l = l_res 
				
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
				elif q <> '':
					q_list.append(q)

				for item_label in item_json["entities"][q]["labels"]:
					item_label_lang = item_json["entities"][q]["labels"][item_label]["language"]
					item_label_value = item_json["entities"][q]["labels"][item_label]["value"]
			
					if item_label_lang in langs or item_label_lang=='en':
						item_label_dict[item_label_lang] = item_label_value

				if "sitelinks" in item_json["entities"][q]:
					for item_link in item_json["entities"][q]["sitelinks"]:
						item_link_lang = item_json["entities"][q]["sitelinks"][item_link]["site"]
						item_link_lang = item_link_lang.replace('wiki','')
						item_link_lang = item_link_lang.replace('be_x_old','be-tarask')
						item_link_value = item_json["entities"][q]["sitelinks"][item_link]["title"]
			
						if item_link_lang in langs or item_link_lang=='en':
							item_link_dict[item_link_lang] = item_link_value


				txt=txt+ u'|-'+'\n'

				if 'en' not in item_label_dict or 'en' not in item_link_dict or item_label_dict['en']=='':
					if en_title != '':
							txt=txt+ u'| '+en_title+'\n'
							print(en_title)
					else:
						if art != '':
							txt=txt+ u'| '+art+'\n'
							print(art)
						else:
							inverse = [(value, key) for key, value in item_label_dict.items()]
							txt=txt+ u'| '+max(inverse)[0]+'\n'
							print(max(inverse)[0])
				else:
					txt=txt+ u'| style="background:#fff8dc"| ' + u'[[:en:'+ item_link_dict['en'] + u'|'+item_label_dict['en']+u']]'+'\n'
					print (item_label_dict['en'])

				if q=='-1':
					txt=txt+ u'| '+'\n'
					stats_orig_list[country] += 1
				else:
					txt=txt+ u'| style="background:#fff8dc"| ' + u'[[:d:'+q+u'|'+q+u']]'+'\n'
					print(q)
					stats_orig_list[country] += 1
		

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
								stats_by_country[country] += 1
								stats_by_lang[key] += 1
			except Exception as e:
				print "".join(traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
		txt=txt+ '|}'+'\n'

	if debug==0:
		savePage('Wikimedia_CEE_Spring_2015/Structure/'+obj, txt)
	else:
		savePage('User:Botik/'+obj, txt)


print(stats_orig_list)
print(stats_by_country)
print(stats_by_lang)

PublishStats()

try:
	f = open('/home/ajvol/pywikibot/forenames/cee_cache.txt', 'w')
	json.dump(cache, f)
	f.close()
except:
	print('Faild to save cache')
