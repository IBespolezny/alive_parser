import requests

cookies = {
    'ASP.NET_SessionId': 'kolpu4a0hpg2q4qpn1my0vzm',
    '_userGUID': '0:mgpe5rsf:X~iBSfSI~rF7fgJcFsQS6Dv2j8pkF7yK',
    'dSesn': '9b681fa0-3308-4062-d298-46c78cf55f77',
    '_dvs': '0:mgpe5rsf:5zKK6O119A9YcdLXp1_b49~vcoZVhPp0',
    '_userGUID': '0:mgpe5rsf:X~iBSfSI~rF7fgJcFsQS6Dv2j8pkF7yK',
    'phone-region': '28159',
    'session_timer_104054': '1',
    'session_timer_104055': '1',
    'session_timer_104056': '1',
    'session_timer_104057': '1',
    'PageNumber': '5',
    '_gcl_au': '1.1.809753926.1760375566',
    'tmr_lvid': 'b2974bae19616b36582c47953a1d8457',
    'tmr_lvidTS': '1757675732216',
    '_ym_uid': '1757675733483228650',
    '_ym_d': '1760375567',
    '_ym_isad': '2',
    '_fbp': 'fb.1.1760375567255.697428114862583849',
    '_ym_visorc': 'w',
    '_tt_enable_cookie': '1',
    '_ttp': '01K7F8YWYTCKY39H956MVP7RV6_.tt.1',
    'ttcsid_CU9KQR3C77UC1F5CMCC0': '1760375567324::NRkpYNkoVJflPrfoKhyA.1.1760375601610.0',
    'ttcsid': '1760375567325::Nl9bSdrn4ZPdcKMiIPCI.1.1760375601610.0',
    '_ga': 'GA1.1.473315785.1760375567',
    '_ga_9G4SE8RW01': 'GS2.1.s1760375566$o1$g1$t1760375708$j43$l0$h0',
    '_ga_LS3F9ECZ7B': 'GS2.1.s1760375566$o1$g1$t1760375708$j60$l0$h254318898',
    'ck_cntrs_hide': 'false',
    '_clck': 'ejjhnt%5E2%5Eg04%5E0%5E2112',
    '_clsk': 'xkziql%5E1760375601743%5E4%5E1%5Eo.clarity.ms%2Fcollect',
    'domain_sid': 'l4B9wAEMniWqmNj2h-Eag%3A1760375568327',
    'tmr_detect': '0%7C1760375602837',
    'seconds_on_page_104054': '137',
    'seconds_on_page_104055': '137',
    'seconds_on_page_104056': '137',
    'seconds_on_page_104057': '137',
    'digi_uc': '|v:176037:10476071',
    'was_called_in_current_session_104054': '1',
    'c2d_widget_id': '{%226a3fff00e8357ecff8a8cc68e5b2dbbf%22:%22{%5C%22client_id%5C%22:%5C%22[chat]%202f98dcb6fa5a0e559ad5%5C%22%2C%5C%22client_token%5C%22:%5C%222f483f7b3d0176db592030281cc4b9f6%5C%22}%22}',
    'was_called_in_current_session_104055': '1',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
    'Accept': '*/*',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Referer': 'https://motorland.by/auto-parts/',
    # 'Cookie': 'ASP.NET_SessionId=kolpu4a0hpg2q4qpn1my0vzm; _userGUID=0:mgpe5rsf:X~iBSfSI~rF7fgJcFsQS6Dv2j8pkF7yK; dSesn=9b681fa0-3308-4062-d298-46c78cf55f77; _dvs=0:mgpe5rsf:5zKK6O119A9YcdLXp1_b49~vcoZVhPp0; _userGUID=0:mgpe5rsf:X~iBSfSI~rF7fgJcFsQS6Dv2j8pkF7yK; phone-region=28159; session_timer_104054=1; session_timer_104055=1; session_timer_104056=1; session_timer_104057=1; PageNumber=5; _gcl_au=1.1.809753926.1760375566; tmr_lvid=b2974bae19616b36582c47953a1d8457; tmr_lvidTS=1757675732216; _ym_uid=1757675733483228650; _ym_d=1760375567; _ym_isad=2; _fbp=fb.1.1760375567255.697428114862583849; _ym_visorc=w; _tt_enable_cookie=1; _ttp=01K7F8YWYTCKY39H956MVP7RV6_.tt.1; ttcsid_CU9KQR3C77UC1F5CMCC0=1760375567324::NRkpYNkoVJflPrfoKhyA.1.1760375601610.0; ttcsid=1760375567325::Nl9bSdrn4ZPdcKMiIPCI.1.1760375601610.0; _ga=GA1.1.473315785.1760375567; _ga_9G4SE8RW01=GS2.1.s1760375566$o1$g1$t1760375708$j43$l0$h0; _ga_LS3F9ECZ7B=GS2.1.s1760375566$o1$g1$t1760375708$j60$l0$h254318898; ck_cntrs_hide=false; _clck=ejjhnt%5E2%5Eg04%5E0%5E2112; _clsk=xkziql%5E1760375601743%5E4%5E1%5Eo.clarity.ms%2Fcollect; domain_sid=l4B9wAEMniWqmNj2h-Eag%3A1760375568327; tmr_detect=0%7C1760375602837; seconds_on_page_104054=137; seconds_on_page_104055=137; seconds_on_page_104056=137; seconds_on_page_104057=137; digi_uc=|v:176037:10476071; was_called_in_current_session_104054=1; c2d_widget_id={%226a3fff00e8357ecff8a8cc68e5b2dbbf%22:%22{%5C%22client_id%5C%22:%5C%22[chat]%202f98dcb6fa5a0e559ad5%5C%22%2C%5C%22client_token%5C%22:%5C%222f483f7b3d0176db592030281cc4b9f6%5C%22}%22}; was_called_in_current_session_104055=1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

response = requests.get('https://motorland.by/auto-parts/', cookies=cookies, headers=headers)

with open('response.html', 'w', encoding='utf-8') as file:
    file.write(response.text)