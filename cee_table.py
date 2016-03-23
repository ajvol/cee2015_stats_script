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

objects = {C:\Anaconda2\python.exe C:/Users/user1/PycharmProjects/cee_stats_script/cee_table.py
+++++++++++Albania
Q4709193
Q1085141
Q1147867
Q581281
Q1075799
Q1968108
Q3303191
Q664356
Q597564
Q4709196
Q4709167
Q5163780
Q3302318
Q5215268
Q924171
Q2754549
Q20081449
Q4709190
Q1051868
Q19573080
Q1199173
Q6524239
Q1161792
Q865835
Q1786972
Q187026
Q695245
Q1521938
Q1157724
Q686088
Q919200
Q2305090
Q733645
Q16900135
Q1969017
Q1729043
Q1973837
Q1725911
Q8055
Q16953117
Q6054803
Q1454570
Q806714
Q16900743
Q10564941
Q4694009
Q21027639
Q1379768
Q4709198
Q180937
Q181037
Q2047966
Q5432163
Q3305597
Q3301000
Q1075302
Q29347
Q186262
Q73996
Q4134683
Q1997543
Q934030
Q257843
Q3056676
Q2076066
Q1820096
Q311155
Q441430
Q472159
Q210183
Q2755449
Q2855705
Q917351
Q3302931
Q5602970
Q467864
Q1814009
Q2305078
Q5354606
Q1135960
Q247604
Q17355584
Q2354948
Q1572318
Q583203
Q718294
Q146715
Q634977
Q582680
Q213833
Q2658979
Q582781
Q4709183
Q281097
Q829597
Q2720692
Q6312406
Q779868
Q240881
Q13041166
Q60489
Q1280589
Q2516917
Q1290184
Q1376434
Q7571819
Q3407236
Q4499389
Q1474287
Q16961466
Q531492
Q13046282
Q22031784
Q2603847
Q3280529
Q7695342
Q5437938
Q2484419
Q1148613
Q678964
Q16931713
Q463521
Q949565
Q21129029
Q7899648
Q7842364
Q834658
Q13634091
Q22809885
Q3301350
Q10481367
Q1280655
Q13045607
Q3300364
Q13042497
+++++++++++Armenia
Q684411
Q684384
Q2665906
Q2860299
Q19681579
Q909438
Q351670
Q2067009
Q247939
Q969702
Q152293
Q4461197
Q254988
Q1399327
Q2632702
Q739349
Q1382698
Q1977392
Q967052
Q2038853
Q311311
Q1382028
Q165648
Q718409
Q1791020
Q683729
Q3653188
Q4074746
Q1971498
Q1054731
Q1264142
Q2604496
Q4466621
Q1779559
Q2202018
Q379831
Q2632883
Q5959435
Q1585409
Q3104777
Q4532395
Q1144630
Q1076666
Q793853
Q2416197
Q211263
Q181932
Q203568
Q4068356
Q2471326
Q737363
Q30548
Q1140988
Q920874
Q13058055
Q2496723
Q13054738
Q15210687
Q1984244
Q207291
Q21083275
Q10637838
Q190223
Q1840481
Q946058
Q1974145
Q4411876
Q2081671
Q79797
Q4252918
Q7449866
Q2382992
Q180636
Q542057
Q154586
Q1398518
Q196219
Q718378
Q77028
Q2389003
Q1875808
Q16370810
Q721589
Q4500313
Q6950938
Q965558
Q965558
Q44625
Q983809
Q932013
Q440802
Q538624
Q569816
Q595285
Q1154808
Q612949
Q612803
Q613051
Q279396
Q320337
Q1579175
Q474526
Q2460414
Q1124922
Q595285
Q193688
Q365695
Q285772
Q201303
Q541848
Q2622868
Q80034
Q1018969
Q2572766
Q733610
Q39560
Q183394
Q429059
Q546010
Q2038742
Q2475091
Q734700
Q762732
Q250652
Q791185
Q139670
Q815567
Q1968443
Q733610
Q164396
Q2064143
Q2503503
Q2624768
Q314043
Q983493
Q331056
Q348006
Q984532
Q318430
Q2074389
Q4068976
Q4070512
Q4137549
Q4152350
Q2379496
Q4176238
Q8052576
Q1018734
Q3056892
Q1474624
Q1977379
Q4139271
Q15267804
Q2082826
Q2033155
Q467164
Q692194
Q1476754
Q13052958
Q7265557
Q14914648
Q1450693
Q5686213
Q1990472
Q1962291
Q952960
Q1971489
Q4154838
Q4165121
Q469893
Q4404999
Q541175
Q2449431
Q4074748
Q2357160
Q4924
Q393151
Q2112831
Q4075096
Q4054419
Q3574447
Q466023
+++++++++++Austria
Q303649
Q42029
Q303779
Q78772
Q2090712
Q41923
Q208208
Q220241
Q609634
Q190348
Q4935045
Q307518
Q679359
Q697907
Q3388
Q251246
Q665816
Q874988
Q701036
Q688715
Q8085
Q4694011
Q302037
Q781832
Q84482
Q700436
Q698639
Q677560
Q586665
Q301890
Q671856
Q225466
Q669743
Q303649
Q258516
Q356289
Q829823
Q18091
Q699412
Q238266
Q295065
Q449997
Q685660
Q685196
Q243017
Q699375
Q1006398
Q179111
Q186867
Q695599
Q475658
Q871363
Q557150
Q700110
Q13564543
Q1763734
Q83822
Q129612
Q117297
Q4852683
Q872485
Q1365717
Q697347
Q15850175
Q2167267
Q3624335
Q518101
Q437303
Q783910
Q78539
Q44517
Q593463
Q352464
Q215122
Q61956
Q61954
Q78589
Q88878
Q5885682
Q89233
Q85641
Q89410
Q78571
Q78858
Q49034
Q113741
Q78506
Q156898
Q78485
Q56189
Q93525
Q112443
Q88839
Q697208
Q698487
Q699091
Q701769
Q129113
Q1600958
Q478455
Q1574072
+++++++++++Azerbaijan
Q570693
Q724091
Q724104
Q4058252
Q724234
Q2427263
Q4058269
Q1996684
Q186413
Q580027
Q936001
Q317397
Q935982
Q4062236
Q2985139
Q2035157
Q344569
Q43928
Q842822
Q338889
Q80499
Q4435307
Q4068343
Q4056818
Q2468888
Q318181
Q593274
Q2383378
Q2468697
Q4524236
Q2468740
Q4433814
Q2060062
Q4186734
Q2060085
Q2060073
Q1630927
Q2060096
Q279878
Q2059257
Q4521162
Q2059240
Q7505463
Q2059251
Q16897717
Q1656522
Q4694012
Q4856333
Q4202085
Q2596160
Q483725
Q5377065
Q2666778
Q1622293
Q190230
Q482942
Q2476230
Q5938150
Q5500740
Q1280476
Q865115
Q2505951
Q94539
Q2738877
Q17004958
Q2612138
Q763213
Q613229
Q723476
Q218074
Q2121616
Q1619674
Q448820
Q311856
Q319380
Q211634
Q312267
Q1330516
Q5340440
Q343572
Q1139612
Q205602
Q330600
Q789921
Q724216
Q16954835
Q1268738
Q1268738
Q617956
Q213271
Q4075924
Q386864
Q1030032
Q619376
Q218738
Q333679
Q188328
Q177076
Q11822220
Q1968443
Q260437
Q1249785
Q379997
Q1642939
Q2268869
Q428400
Q324470
Q555994
Q406684
Q875512
Q926447
Q2568851
Q2988180
Q4158590
Q218446
Q734004
Q129207
Q4201721
Q752128
Q2024702
Q4279819
Q1985760
Q8031410
Q4075909
Q234304
Q2507445
+++++++++++Belarus
Q1445079
Q236983
Q12079348
Q4070858
Q3917391
Q16862908
Q2568026
Q4408702
Q19425048
Q15989666
Q19347338
Q19347339
Q2470349
Q13033442
Q13028145
Q2499892
Q719422
Q1532456
Q209643
Q15989679
Q950155
Q4235754
Q2465016
Q1661800
Q3919049
Q2986701
Q770907
Q2657165
Q3919081
Q2630583
Q2157205
Q23868
Q1710170
Q2468464
Q2634748
Q2786026
Q13031491
Q4235752
Q6031766
Q6315031
Q13133440
Q10921873
Q13032687
Q2659535
Q3313957
Q2656838
Q19284177
Q3919067
Q13031172
Q946248
Q2074888
Q19692565
Q1990060
Q3919194
Q5575704
Q5578101
Q18246441
Q18907600
Q1982859
Q13028295
Q3812749
Q5414778
Q13030667
Q1591054
Q16744078
Q2579175
Q2576505
Q2588857
Q2502875
Q1742825
Q1742825
Q17484689
Q2376002
Q2561905
Q1429567
Q3917485
Q2034395
Q2584571
Q6511262
Q2073524
Q3919319
Q4082744
Q13031503
Q9708
Q11710682
Q316109
Q6472319
Q18509245
Q13028791
Q3918454
Q19810311
Q6468540
Q1850480
Q4082756
Q23290732
Q941595
Q1376763
Q211247
Q561635
Q3646572
Q435320
Q45087
Q2662397
Q2636360
Q1354627
Q941622
Q2509630
Q2996666
Q2993939
Q3008609
Q2590303
Q79822
Q2976584
Q472576
Q2623476
Q471207
Q377
Q483709
Q1392368
Q2623476
Q2662384
Q2623476
Q3920081
Q1972194
Q93284
Q2662343
Q2500853
Q2419271
Q335794
Q508975
Q52488
Q2473134
Q2986268
Q2991169
Q2858143
Q77430
Q3920276
Q13387
Q3920249
Q3920148
Q2634627
Q1116540
Q11834038
Q280686
Q13469680
Q21712762
Q21711103
Q21711106
Q21684129
Q21711096
Q18015630
Q1322583
Q117504
Q181376
Q2678
Q140147
Q102217
Q154835
Q207294
Q208609
Q863576
Q739491
Q954114
Q954948
Q744167
Q539012
Q200917
Q955992
Q1579605
Q747554
Q81091
Q3920824
Q209993
Q1902968
Q160680
Q431491
Q3918715
Q3920875
Q13030300
Q2662336
Q2415464
Q1145443
Q2035872
Q751342
Q1365037
Q2078746
Q727829
Q4403
Q1142159
Q4350644
Q863096
Q186252
Q1130487
Q4439085
Q191101
Q355825
Q446994
Q376296
Q3518480
Q1155906
Q1061500
Q1861453
Q1771643
Q14921981
Q1798607
Q997640
Q1155906
Q132633
Q179602
Q668988
Q2376574
Q1049659
Q143637
Q2094034
Q168867
Q168859
Q554899
Q3495280
Q475004
Q2991206
Q2150090
Q2995798
Q704477
Q1361912
Q314338
Q1392488
Q561617
Q76987
Q777855
Q815314
Q801196
Q232164
Q275396
Q13211
Q4533022
Q2997706
Q345194
Q3920350
Q16694265
Q2635667
Q311995
Q517333
Q671362
Q2419712
Q49683
Q197806
Q205109
Q172107
Q845668
Q849176
Q1378225
Q473670
Q3918294
Q3917425
Q4881959
Q842199
Q2895
Q13033080
Q2337514
Q13033079
Q277788
Q11150089
Q2498541
Q242436
Q244852
Q336754
Q218186
Q967015
Q54030
Q727122
Q191479
Q2662405
Q709977
Q710236
Q2350484
Q633997
Q1967977
Q7029745
Q458245
Q976045
Q381755
Q45305
Q310347
Q4220497
Q877583
Q816145
Q1779755
Q1779755
Q2418908
Q815268
Q816145
Q2298294
Q257706
Q233823
Q2566534
Q294136
Q240174
Q2607554
Q2986655
Q3920741
Q2510833
Q2024023
Q454901
Q221575
Q274334
Q209193
Q10118
Q2414267
+++++++++++Bosnia and Herzegovina
Traceback (most recent call last):
  File "C:/Users/user1/PycharmProjects/cee_stats_script/cee_table.py", line 236, in <module>
    wiki_text = co_list_json["query"]["pages"][itm]["revisions"][0]["*"]
KeyError: 'revisions'

+++++++++++Bulgaria
Q2499614
Q1331407
Q524741
Q3657731
Q910713
Q207945
Q573222
Q47020
Q43282
Q351805
Q946052
Q2024346
Q1536036
Q301815
Q319296
Q59893
Q512147
Q2990814
Q2663966
Q12274312
Q2126234
Q8209
Q12274290
Q3269914
Q12283453
Q2991178
Q631641
Q2915220
Q1858012
Q12288872
Q310630
Q1284754
Q1898224
Q5923768
Q1256887
Q2448853
Q1084236
Q956441
Q382033
Q2477881
Q1509177
Q528781
Q2048895
Q1866762
Q362106
Q363430
Q12282452
Q2989196
Q526382
Q2000883
Q7849377
Q2006747
Q4179524
Q14633979
Q12284217
Q535200
Q2332524
Q2332524
Q527920
Q357980
Q1225859
Q712741
Q935407
Q12290574
Q653803
Q12274689
Q3657167
Q5598716
Q1408968
Q12287885
Q301815
Q6993182
Q276553
Q1497827
Q2991178
Q12279993
Q6974996
Q5327147
Q6974486
Q1066518
Q1968325
Q2023134
Q12287456
Q12292240
Q3334309
Q688677
Q2663966
Q2654627
Q6940953
Q1892609
Q2006052
Q11037391
Q790052
Q3409197
Q803919
Q3702610
Q942127
Q841744
Q387580
Q736824
Q570038
Q731972
Q928361
Q205169
Q12282545
Q6434689
Q12294984
Q12294086
Q250170
Q16852506
Q15635457
Q2996775
Q12282731
Q12273425
Q12273417
Q2009256
Q12297082
Q18922477
Q3042471
Q1866826
Q12286625
Q12287205
Q206918
Q19029
Q19706491
Q1412833
Q12289529
Q20497431
Q12292267
Q20497774
Q20497796
Q12299302
Q1089051
Q12279669
Q12284060
Q3553990
Q12279211
Q13557581
Q931946
Q106612
Q19705097
Q744983
Q20498216
Q12294105
Q4879992
Q13317
Q3042478
Q6778243
Q1943549
Q12273078
Q12296839
Q1884722
Q9212809
Q1140684
Q209341
Q262677
Q768480
Q12299068
Q286604
Q3244593
Q12289412
Q12274952
Q4996297
Q651314
Q748637
Q1887045
Q41741
Q182660
Q199499
Q459
Q6509
Q6506
Q173474
Q191795
Q726158
Q6489
Q170427
Q378943
Q500954
Q217805
Q204347
Q193904
Q2890912
Q2119511
Q204127
Q753919
Q731777
Q217126
Q122082
Q12292252
Q12291458
Q3657749
Q1902334
Q670939
Q1032792
Q894120
Q822130
Q610143
Q172540
Q74687
Q5286727
Q6395796
Q1026748
Q2048727
Q2370447
Q1022285
Q2036915
Q19368993
Q20497049
Q6647812
Q2036915
Q3905627
Q1004060
Q165189
Q133255
Q242758
Q742770
Q204095
Q1145659
Q187125
Q170235
Q337681
Q887271
Q172798
Q2833189
Q735336
Q1385212
Q2271936
Q342424
Q1725236
Q313833
Q276567
Q28517
Q159585
Q155074
Q119989
Q1371792
Q1276487
Q127951
Q234707
Q3658556
Q2561683
Q2119886
Q2095010
Q12296856
Q1004006
Q1370380
Q1567857
Q16955362
Q1423410
Q7916008
Q12298878
Q1567774
Q1324587
Q203004
Q12291469
Q3441843
Q2875909
Q20500120
Q12291466
Q1077240
Q7928092
Q476274
Q2880826
Q429846
Q429759
Q429538
Q429398
Q429141
Q65338
Q622059
Q1145682
Q177918
Q184183
Q2042945
Q2451496
Q1004004
Q318461
Q488297
Q360160
Q983917
Q459780
Q7800
Q203817
Q420759
Q158504
Q311057
Q350061
Q1281955
Q270740
Q194113
Q192264
Q347118
Q583420
Q12287716
Q6088995
Q552756
Q2915222
Q59893
Q3251089
Q1363208
Q1003730
Q799313
Q2606872
Q2071240
Q12283571
Q15733285
Q545553
Q19803333
Q4751826
Q12298241
Q20747446
Q1656381
Q12295513
Q3510054
Q4069764
Q5321471
Q12292204
Q12292173
Q363088
Q1225834
Q20497614
Q1509188
Q2079726
Q4093313
Q759207
Q5277447
Q646605
Q1898224
Q12296474
Q20500460
Q382140
Q12278612
Q12286579
Q12274857
Q12290364
Q4804164
Q355471
Q11816052
Q12287039
Q6660963
Q3658709
Q4416121
Q12290471
Q12295195
Q4517847
Q5547198
Q6565227
Q12274302
Q3655857
Q4996297
Q7683138
Q2621317
Q2071240
Q1696952
Q4996185
Q3655956
Q12290810
Q3658227
Q2370447
Q11265144
Q5364165
Q2606872
Q1275965
Q4996244
Q906624
Q7243408
Q841581
Q257325
Q12273454
Q469033
Q288999
Q3492899
Q268934
Q270584
Q230850
Q233410
Q6378552
Q265277
Q4245551
Q270016
Q438291
Q6851258
Q7003844
Q265139
Q258130
Q232008
Q7620742
Q19509324
Q137892
Q210724
Q438291
Q233410
Q434589
Q258130
Q270596
Q436011
Q12281328
Q3721467
Q458360
Q2827062
Q4454893
Q12274470
Q4309439
Q11722438
Q6285916
Q6280160
Q88015
Q700589
Q4380347
Q3655901
Q6849793
Q4284172
Q1996655
Q84509
Q254641
Q4127042
Q2984651
Q44625
Q694801
Q1568321
Q6280160
Q18636543
Q12278713
Q12292644
Q21962212
Q12280733
Q3242108
Q12272473
Q5111623
Q12295154
Q12294502
Q12276451
Q463311
Q12290611
Q2901020
Q12280659
Q12278178
Q12292619
Q12280936
Q12291098
+++++++++++Croatia
Q2748196
Q1789628
Q3510323
Q312220
Q402221
Q426935
Q1140629
Q16114046
Q926442
Q3182749
Q317588
Q1525417
Q2585366
Q1075789
Q1266673
Q468219
Q215923
Q3435941
Q591878
Q743452
Q756987
Q20526247
Q189849
Q223275
Q5707
Q319276
Q272009
Q1118811
Q341487
Q142894
Q26360
Q8067
Q898224
Q140388
Q894110
Q2005561
Q2028046
Q1892360
Q3127176
Q866463
Q3133224
Q3069294
Q339789
Q1664911
Q595751
Q1509011
Q167420
Q2047394
Q2035486
Q1191920
Q4376184
Q3509326
Q134479
Q639266
Q311903
Q209982
Q204279
Q1154532
Q1278383
Q371576
Q5468473
Q15145562
Q571619
Q128016
Q931988
Q583140
Q2381904
Q1125392
Q210726
Q68969
Q154418
Q310505
Q3042828
Q606632
Q694379
Q2893431
Q1264085
Q9036
Q310757
Q7334368
Q893186
Q1287538
Q1281664
Q1302535
Q1861667
Q243445
Q675848
Q609301
Q3439910
Q631375
Q3512583
Q210814
Q2661542
Q6379
Q909902
Q254383
Q7383707
Q455515
Q452807
Q452694
Q744439
+++++++++++Czech Republic
Q193369
Q204871
Q1535529
Q5949
Q421678
Q12256
Q735278
Q2164919
Q2142483
Q266698
Q744016
Q200693
Q513821
Q913185
Q1012808
Q1014747
Q1012711
Q1013458
Q1013039
Q508519
Q1755820
Q1012726
Q940492
Q45033
Q118256
Q655633
Q921344
Q457453
Q826452
Q2164885
Q742362
Q752318
Q61332
Q388362
Q1488700
Q1100429
Q80843
Q472688
Q61965
Q2420392
Q2334312
Q2717859
Q764794
Q506594
Q1164329
Q1129608
Q244816
Q555682
Q44323
Q84250
Q282445
Q12046674
Q12033659
Q11282590
Q12020917
Q12045741
Q13638362
Q11282622
Q341071
Q11282408
Q11282497
Q11282282
Q12045878
Q12020572
Q12020572
Q1786390
Q350426
Q710504
Q12735
Q508939
Q159642
Q157970
Q3505812
Q161368
Q745363
Q461104
Q156321
Q594896
Q274171
Q239704
Q2171796
Q1445713
Q713271
Q539798
Q338826
Q981157
Q12054578
Q1377687
Q155855
Q560390
Q471184
Q949091
Q93166
Q1669800
Q333741
Q239925
Q317916
Q550001
Q43977
Q434550
Q713261
Q283121
Q158354
Q220550
Q545818
Q452084
Q361265
Q352914
Q634100
Q740181
Q175285
Q942980
Q608774
Q712420
Q109067
Q2754
Q102483
Q158379
Q699619
Q709680
Q471450
Q1354569
Q242130
Q163557
Q258715
Q36233
Q506582
Q543319
Q426528
Q975764
Q439209
Q471209
Q142059
Q234893
Q905
Q51525
Q235032
Q352030
Q2980777
Q2602324
Q706451
Q1374327
Q1066361
Q1729166
Q471434
Q282000
Q984033
Q967970
Q769826
Q169065
Q362319
Q169027
Q316165
Q738526
Q1141186
Q966754
Q1781740
Q332869
Q341302
Q2356541
Q153455
Q311387
Q156033
Q313974
Q157777
Q357172
Q48173
Q7298
Q184933
Q223258
Q312700
Q347611
Q117110
Q366711
Q78530
Q7304
Q158017
Q360863
Q161328
Q354927
Q316549
Q1776937
Q366671
Q356687
Q356151
Q83179
Q267324
Q333187
Q1044709
Q11985
Q6440910
Q552113
Q446631
Q728117
Q700163
Q558499
Q448555
Q695377
Q687347
Q955415
Q446948
Q740396
Q980407
Q146691
Q159074
Q957157
Q698151
Q687335
Q167414
Q454568
Q271743
Q368484
Q179071
Q12042406
Q699793
Q950570
Q1356243
Q287703
Q918352
Q168974
Q76718
Q700589
Q311931
Q550722
Q1337801
Q402282
Q559795
Q381720
Q1938506
Q508620
Q78553
Q78564
Q159542
Q379593
Q379601
Q78558
Q526022
Q1398717
Q470581
Q963023
Q1109649
Q78926
Q1640623
Q157701
Q730128
Q62627
Q254985
Q553419
Q41390
Q37970
Q58586
Q9215
Q52589
Q295345
Q54545
Q182736
Q30812
Q223158
Q171295
Q204978
Q483137
Q193187
Q233683
Q231036
Q6419
Q312695
Q317431
Q374824
Q229503
Q236315
Q29162
Q180581
Q229121
Q352017
Q266489
Q446177
Q1336822
Q388631
Q193665
Q81502
Q1155216
Q11995745
Q1819381
Q3409229
Q5015587
Q3210181
Q389423
Q5068060
Q320265
Q2347172
Q17149373
Q29032
Q890971
Q12022546
Q6850754
Q1128501
Q10728124
Q341148
Q651129
Q913567
Q828099
Q1142687
Q631218
Q341085
Q14923603
Q78492
Q152274
Q296054
Q371854
Q310000
Q57434
Q162401
Q729362
Q182817
Q1059215
Q542945
Q605324
Q715264
Q1854586
Q478301
Q287652
Q4373
Q193152
Q149427
Q1137957
Q1773668
Q19776284
Q155669
Q159679
Q150586
Q153545
Q140359
Q215968
Q154255
Q274152
Q192893
Q42585
Q35499
Q152750
Q839710
Q610179
Q666778
Q315531
Q455948
Q1085
Q14960
Q8385
Q43453
Q146351
Q81137
Q156974
Q16506
Q180139
Q36989
Q183111
Q171018
Q384544

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
