#!/usr/bin/env python
# coding: utf-8

# # 용인시 지역별 상권분석을 통한 청년창업 지원 대책 도출
# 
# 분석 목적 : 
# - 지역별 청년 사업체 실태를 쉽고 명확히 보이도록 시각화
# - 청년 창업 또는 사업 정착을 위한 아이디어 제시
# 
# 분석 규격 : 
# - 좌표계 : WGS84 (epsg:4326)
# - 엔코딩 : utf-8

# ## 필요한 라이브러리 import

# In[172]:


# 데이터 
import numpy as np
import pandas as pd
import json
import pathlib
from shapely.geometry import Polygon, LineString, Point
from pyproj import CRS
from shapely import wkt

# 시각화 라이브러리
get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib.pyplot as plt

import matplotlib as mpl
import os
from matplotlib import font_manager as fm, rcParams


# 지도 시각화 라이브러리 
import geopandas as gpd
import folium




# In[122]:


# matplot 한글 패치
fm.get_fontconfig_fonts()
font_location = './font/NanumGothic.ttf' # For Windows, NanumGothic.ttf 설치 필요(네이버 무료 폰트)
font_name = fm.FontProperties(fname=font_location).get_name()
mpl.rc('font', family=font_name)


# In[68]:


# 데이터 가져오기 위한 api 
from geoband.API import *

## 데이터를 경로에 다운로드 함
input_path = pathlib.Path('./input')
if not input_path.is_dir():
    input_path.mkdir()

GetCompasData('SBJ_2012_002', '1', input_path.joinpath('1.용인시_상권_정보.csv'))
GetCompasData('SBJ_2012_002', '2', input_path.joinpath('2.용인시_상권_업종코드.csv'))
GetCompasData('SBJ_2012_002', '3', input_path.joinpath('3.용인시_인구정보(총인구수)_격자.geojson'))
GetCompasData('SBJ_2012_002', '4', input_path.joinpath('4.용인시_인구정보(고령)_격자.geojson'))
GetCompasData('SBJ_2012_002', '5', input_path.joinpath('5.용인시_인구정보(생산가능)_격자.geojson'))
GetCompasData('SBJ_2012_002', '6', input_path.joinpath('6.용인시_인구정보(유소년)_격자.geojson'))
GetCompasData('SBJ_2012_002', '7', input_path.joinpath('7.용인시_유동인구.csv'))
GetCompasData('SBJ_2012_002', '11', input_path.joinpath('11.용인시_법정경계(시군구).geojson'))
GetCompasData('SBJ_2012_002', '13', input_path.joinpath('13.용인시_행정경계(읍면동).geojson'))
GetCompasData('SBJ_2012_002', '16', input_path.joinpath('16.용인시_소상공인_매출정보.geojson'))
GetCompasData('SBJ_2012_002', '17', input_path.joinpath('17.용인시_소상공인_매출정보.csv'))

for path in list(input_path.glob('*.csv')) + list(input_path.glob('*.geojson')):
    print(path)


# ## 상권 정보 데이터 전처리
# 
# ### 1) 상권정보 point로 변환하여 격자 id(gid) 컬럼 붙이기

# In[25]:


## 상권 정보 불러오기 
sg_data = gpd.read_file('./input/1.용인시_상권_정보.csv', encoding='utf-8')

## 경도, 위도 컬럼으로 point 만들어주기
sg_data['경도'] = sg_data['경도'].astype(float)
sg_data['위도'] = sg_data['위도'].astype(float)
sg_data['geometry'] = sg_data.apply(lambda row : Point([row['경도'], row['위도']]), axis=1) 


# In[26]:


## 소상공인 격자 데이터 불러오기
ssgi_geo_data = gpd.read_file('./input/16.용인시_소상공인_매출정보.geojson')
ssgi_geo_data = ssgi_geo_data.set_geometry('geometry')


# In[27]:


## row, columns 수 확인
print('ssgi_geo_data.shape : ' , ssgi_geo_data.shape)
print('sg_data.shape : ' , sg_data.shape)


# In[28]:


## sjoin (공간 조인) 
sg_data_gid = gpd.sjoin(ssgi_geo_data[['gid','geometry']], sg_data, how='left', op = 'contains' )
sg_data_gid.drop(columns=['index_right'])
sg_data_gid.to_csv('./input/용인시_상권정보_gid.csv', encoding='utf-8', index=False)
sg_data_gid.head()


# ### 2) 격자별 업종별 사업체 수 집계하기

# In[30]:


# 격자별 업종별 사업체 수 
sg_data_count = pd.pivot_table(sg_data_gid, index =['gid'], columns=['대분류코드'],aggfunc = 'count', fill_value = 0)
sg_data_count = sg_data_count['geometry']
sg_data_count = sg_data_count.reset_index()
sg_data_count = sg_data_count.rename({'D':'소매', 'F':'생활서비스', 'L':'부동산','N':'관광/여가/오락','O':'숙박',
                                      'P':'스포츠', 'Q':'음식','R':'학문/교육'}, axis=1)
sg_data_count.to_csv('./input/용인시_격자_업종별(대분류)_사업체수.csv', encoding='utf-8', index=False)
sg_data_count


# In[127]:


sg_data_count1 = pd.DataFrame(sg_data_count.sum())
sg_data_count1 = sg_data_count1.drop('gid',axis=0)
sg_data_count1 = sg_data_count1.reset_index()
sg_data_count1


# In[141]:


# 격자별 업종별 사업체 수 
sg_data_count2 = pd.pivot_table(sg_data_gid[sg_data_gid['대분류코드']=='Q'], index =['gid'], columns=['중분류코드'],aggfunc = 'count', fill_value = 0)
sg_data_count2 = sg_data_count2['geometry']
sg_data_count2 = sg_data_count2.reset_index()
#g_data_count.to_csv('./input/용인시_격자_업종별(대분류)_사업체수.csv', encoding='utf-8', index=False)
sg_data_count2


# In[142]:


sg_data_count3 = pd.DataFrame(sg_data_count2.sum())
sg_data_count3 = sg_data_count3.drop('gid',axis=0)
sg_data_count3 = sg_data_count3.reset_index()
sg_data_count3


# In[143]:


# 격자별 업종별 사업체 수 
sg_data_count4 = pd.pivot_table(sg_data_gid[sg_data_gid['대분류코드']=='D'], index =['gid'], columns=['중분류코드'],aggfunc = 'count', fill_value = 0)
sg_data_count4 = sg_data_count4['geometry']
sg_data_count4 = sg_data_count4.reset_index()
#g_data_count.to_csv('./input/용인시_격자_업종별(대분류)_사업체수.csv', encoding='utf-8', index=False)
sg_data_count4


# In[144]:


sg_data_count5 = pd.DataFrame(sg_data_count4.sum())
sg_data_count5 = sg_data_count5.drop('gid',axis=0)
sg_data_count5 = sg_data_count5.reset_index()
sg_data_count5


# In[147]:


sg_data_count_m = pd.pivot_table(sg_data_gid, index =['gid'], columns=['중분류코드'],aggfunc = 'count', fill_value = 0)
sg_data_count_m = sg_data_count_m['geometry']
sg_data_count_m = sg_data_count_m.reset_index()
sg_data_count_m = sg_data_count_m.rename({'D03':'종합소매점', 'D05':'의복의류', 'Q01':'한식','Q12':'커피점/카페'}, axis=1)

sg_data_count_m = sg_data_count_m[['gid','종합소매점','의복의류','한식','커피점/카페']]
sg_data_count_m


# ## 유동인구 데이터 전처리

# ### 1) 유동인구 데이터 250m 격자에 넣고 합하기

# In[33]:


## 유동인구 정보 불러오기 
yd_ingu = gpd.read_file('./input/7.용인시_유동인구.csv', encoding='utf-8')

## 경도, 위도 컬럼으로 point 만들어주기
yd_ingu['lon'] = yd_ingu['lon'].astype(float)
yd_ingu['lat'] = yd_ingu['lat'].astype(float)
yd_ingu['geometry'] = yd_ingu.apply(lambda row : Point([row['lon'], row['lat']]), axis=1) 


# In[34]:


## sjoin (공간 조인) 
yd_ingu_gid = gpd.sjoin(ssgi_geo_data[['gid','geometry']], yd_ingu, how='left', op = 'contains' )
yd_ingu_gid.to_csv('./input/용인시_유동인구_gid.csv', encoding='utf-8', index=False)
yd_ingu_gid.to_file('./input/용인시_유동인구_gid.geojson', encoding='utf-8', index=False, driver='GeoJSON')


# In[35]:


yd_ingu.shape


# In[36]:


## yd_ingu_gid 불러오기(geometry 설정해서)
yd_ingu_gid = pd.read_csv('./input/용인시_유동인구_gid.csv', encoding='utf-8')
yd_ingu_gid['geometry'] = yd_ingu_gid['geometry'].apply(wkt.loads)
yd_ingu_gid.set_geometry('geometry')


# In[39]:


## 격자별 월별 유동인구 집계(sum) + 저장하기
yd_ingu_gid = pd.read_csv('./input/용인시_유동인구_gid.csv', encoding='utf-8')
yd_ingu_month = yd_ingu_gid.groupby(['gid','geometry','STD_YM']).sum()
yd_ingu_month = yd_ingu_month.reset_index()
yd_ingu_month = yd_ingu_month.drop(columns=['index_right','lon', 'lat'])
yd_ingu_month.to_csv('./input/용인시_유동인구_gid_월별.csv', encoding='utf-8', index=False)
#yd_ingu_month.to_file('./input/용인시_유동인구_gid_월별.geojson', encoding='utf-8', index=False, driver='GeoJSON')
yd_ingu_month.head()


# In[40]:


## 격자별 2019년 유동인구 집계(sum) + 저장하기
yd_ingu_2019 = yd_ingu_gid.groupby(['gid' , 'geometry']).sum()
yd_ingu_2019 = yd_ingu_2019.reset_index()
yd_ingu_2019 = yd_ingu_2019.drop(columns=['index_right','lon', 'lat'])
yd_ingu_2019.to_csv('./input/용인시_유동인구_gid_2019.csv', encoding='utf-8', index=False)
yd_ingu_2019.head()


# In[ ]:


## yd_ingu_gid 불러오기 (geometry 설정해서)
yd_ingu_month = pd.read_csv('./input/용인시_유동인구_gid_월별.csv', encoding='utf-8')
yd_ingu_month['geometry'] = yd_ingu_month['geometry'].apply(wkt.loads)
yd_ingu_month.set_geometry('geometry')


# In[41]:


#print(yd_ingu.shape)
print(yd_ingu_gid.shape)
print(yd_ingu_month.shape)
print(yd_ingu_2019.shape)


# ### 2) 시간대별(새벽, 아침, 오전, 오후, 저녁, 밤) 유동인구를 집계함

# In[42]:


## 2019년 시간대별 유동인구 
yd_ingu_2019['새벽'] = yd_ingu_2019.apply(lambda row : row['TMST_04'] + row['TMST_05'] + row['TMST_06'] , axis=1) 
yd_ingu_2019['아침'] = yd_ingu_2019.apply(lambda row : row['TMST_07'] + row['TMST_08'] , axis=1) 
yd_ingu_2019['오전'] = yd_ingu_2019.apply(lambda row : row['TMST_09'] + row['TMST_10'] + row['TMST_11'] , axis=1) 
yd_ingu_2019['오후'] = yd_ingu_2019.apply(lambda row : row['TMST_12'] + row['TMST_13'] + row['TMST_14'] + row['TMST_15']+ row['TMST_16']+ row['TMST_17']   , axis=1) 
yd_ingu_2019['저녁'] = yd_ingu_2019.apply(lambda row : row['TMST_18'] + row['TMST_19'] , axis=1) 
yd_ingu_2019['밤'] = yd_ingu_2019.apply(lambda row : row['TMST_20'] + row['TMST_21'] + row['TMST_22']+ row['TMST_23'] + row['TMST_00']
                                       + row['TMST_01']+ row['TMST_02'] + row['TMST_03']  , axis=1) 

yd_ingu_2019_time = yd_ingu_2019[['gid', 'geometry', '새벽', '아침', '오전', '오후', '저녁', '밤']]
yd_ingu_2019_time.to_csv('./input/용인시_유동인구_gid_2019_시간대별.csv', encoding='utf-8', index=False)
yd_ingu_2019_time.head()


# ### 3) 격자별 혼잡시간대

# In[43]:


yd_ingu_2019_time = pd.read_csv('./input/용인시_유동인구_gid_2019_시간대별.csv', encoding='utf-8')
yd_ingu_2019_time = yd_ingu_2019_time.drop(columns=['geometry'])
yd_ingu_2019_time = yd_ingu_2019_time.set_index(['gid'])
yd_ingu_2019_time['혼잡시간대'] = yd_ingu_2019_time.idxmax(axis=1)

yd_ingu_2019_time.head()


# In[44]:


## 유동인구가 아예 없는 격자 -> 혼잡시간대 = '새벽'으로 들어 있어서 'nan' 으로 변경
yd_ingu_2019_time = yd_ingu_2019_time.reset_index()
yd_ingu_2019_time['혼잡시간대'] = yd_ingu_2019_time.apply(lambda row : None if (row['새벽'] + row['아침'] + row['오전'] +row['오후'] + row['저녁'] + row['밤']    ) == 0  else row['혼잡시간대'] , axis=1) 


# In[45]:


yd_ingu_2019_time.head()


# In[46]:


## 용인시_격자별_혼잡시간대 저장
yd_ingu_2019_time.to_csv('./input/용인시_격자별_혼잡시간대.csv', encoding='utf-8', index=False)


# ## 소상공인데이터 전처리

# ### 1)격자별 주 카드 사용자
# 
# 카드사용자 연령대별 비중을 이용해 격자별 카드사용자의 주 연령대를 확인함.

# In[148]:


## 소상공인 격자 데이터 불러오기
ssgi_geo_data = gpd.read_file('./input/16.용인시_소상공인_매출정보.geojson')
ssgi_geo_data = ssgi_geo_data.set_geometry('geometry')


# In[149]:


## 카드_주연령대 컬럼 만들어서 붙이기 
ssgi_card_age = ssgi_geo_data[['gid', 'age10_ratio', 'age20_ratio', 'age30_ratio','age40_ratio', 'age50_ratio', 'age60_ratio', 'age70_ratio']]
ssgi_card_age = ssgi_card_age.set_index(['gid'])
ssgi_card_age['카드_주연령대'] = ssgi_card_age.idxmax(axis=1)
ssgi_card_age['카드_주연령대'] = ssgi_card_age['카드_주연령대'].apply(lambda x : '20대' if x == 'age20_ratio' else( '30대' if x =='age30_ratio' else '40대' if x == 'age40_ratio' else ('50대'  if x == 'age50_ratio' else ('60대' if x =='age60_ratio' else x))))
ssgi_card_age = ssgi_card_age.reset_index()
ssgi_card_age = ssgi_card_age.rename({'age10_ratio':'10대','age20_ratio': '20대','age30_ratio': '30대','age40_ratio':'40대'
                                             ,'age50_ratio':'50대','age60_ratio':'60대','age70_ratio':'70대 이상'}, axis=1)
ssgi_card_age


# In[85]:


## 격자별 카드 주연령대 저장하기
ssgi_card_age.to_csv('./input/격자별_카드_주연령대 .csv', encoding='utf-8', index=False)


# ### 2) 전년대비 증감률 구하기
# 
# 격자별 전년대비 소상공인 매출 증감률을 통해 매출이 증가하며 상권이 살아나는 지역, 매출이 감소하며 상권이 침체되는 지역을 살펴봄.  
# 동기간 비교를 위해 1~3분기의 매출액을 1년 총 매출액으로 가정함. (2020년 3분기 매출까지 있음)  
# 증감률 = (당해 매출액 -전년도 매출액)/ 전년도 매출액 * 100  

# In[150]:


## 연도별 매출액 합계
ssgi_geo_data['sales_est_amt_2017'] = ssgi_geo_data.apply(lambda row : row['sales_est_amt_201703']+ row['sales_est_amt_201706']+ row['sales_est_amt_201709']  , axis=1) 
ssgi_geo_data['sales_est_amt_2018'] = ssgi_geo_data.apply(lambda row : row['sales_est_amt_201803']+ row['sales_est_amt_201806']+ row['sales_est_amt_201809']  , axis=1) 
ssgi_geo_data['sales_est_amt_2019'] = ssgi_geo_data.apply(lambda row : row['sales_est_amt_201903']+ row['sales_est_amt_201906']+ row['sales_est_amt_201909']  , axis=1) 
ssgi_geo_data['sales_est_amt_2020'] = ssgi_geo_data.apply(lambda row : row['sales_est_amt_202003']+ row['sales_est_amt_202006']+ row['sales_est_amt_202009']  , axis=1)

## 전년대비 증감률(2018, 2019, 2020) 구하기 
ssgi_geo_data['sales_est_rate_2018'] = ssgi_geo_data.apply(lambda row : (row['sales_est_amt_2018']- row['sales_est_amt_2017'])/ row['sales_est_amt_2017'] * 100  if row['sales_est_amt_2017'] != 0  else 0, axis=1) 
ssgi_geo_data['sales_est_rate_2019'] = ssgi_geo_data.apply(lambda row : (row['sales_est_amt_2019']- row['sales_est_amt_2018'])/ row['sales_est_amt_2018'] * 100  if row['sales_est_amt_2018'] != 0  else 0, axis=1) 
ssgi_geo_data['sales_est_rate_2020'] = ssgi_geo_data.apply(lambda row : (row['sales_est_amt_2020']- row['sales_est_amt_2019'])/ row['sales_est_amt_2019'] * 100  if row['sales_est_amt_2018'] != 0  else 0, axis=1)


# ### 4) 소상공인 매출 데이터에 필요한 데이터 붙이기

# In[151]:


# left join

# 업종별(대분류) 사업체 수 붙이기
ssgi_geo_data = pd.merge(ssgi_geo_data,sg_data_count, on='gid', how='left')

# 업종별(중분류) 사업체 수 붙이기
ssgi_geo_data = pd.merge(ssgi_geo_data,sg_data_count_m, on='gid', how='left')

# 혼잡시간대 
ssgi_geo_data = pd.merge(ssgi_geo_data ,yd_ingu_2019_time, on='gid' , how = 'left' )
# 카드 주 연령대
ssgi_geo_data = pd.merge(ssgi_geo_data ,ssgi_card_age, on='gid' , how = 'left' )

ssgi_geo_data.head()


# In[152]:


## '혼잡시간대_카드_주연령대' 만들기

ssgi_geo_data['혼잡시간대_카드_주연령대'] = ssgi_geo_data.apply(lambda row : str(row['혼잡시간대'])+ ' - '+str(row['카드_주연령대'])  , axis=1) 


# In[153]:


ssgi_geo_data.columns


# In[154]:


## 완성된 테이블 저장하기
ssgi_geo_data.to_file('./input/용인시_격자데이터_최종.geojson',driver='GeoJSON')


# ### - '용인시_격자데이터_최종' 불러오기

# In[173]:


## ssgi_geo_data gpd로 가져오기
ssgi_geo_data = gpd.read_file('./input/용인시_격자데이터_최종.geojson')
ssgi_geo_data = ssgi_geo_data.set_geometry('geometry')


# In[174]:


## ssgi_geo_data2 는 json으로 가져오기
ssgi_geo_data_path ="./input/용인시_격자데이터_최종.geojson"
ssgi_geo_data2 = json.load(open(ssgi_geo_data_path, encoding="utf-8"))


# In[160]:


ssgi_geo_data.shape


# ## 시각화

# ### 1) 시군구/행정동 지도 시각화

# In[ ]:




# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')




# 시군구 경계 추가
geo_path_sigungu ="./input/11.용인시_법정경계(시군구).geojson"
geo_sigungu = json.load(open(geo_path_sigungu, encoding="utf-8"))


style_function = lambda x: {'fillColor': '#ffffff', 'fill_opacity' : '0.1'}
folium.GeoJson(geo_sigungu, name='sigungu', style_function=style_function).add_to(map)

# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson" 
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8")) # 1. 행정동 경계 데이터 불러오기

style_function = lambda x: {'fillColor': '#ffffff', 'fill_opacity' : '0.1', 'weight':'0.8'} # 행정동 경계 스타일
hjd = folium.GeoJson(geo_hjd, name='hjg', style_function=style_function).add_to(map) # 행정동 경계 지도에 추가하기
folium.features.GeoJsonTooltip(fields=['ADM_DR_NM'], labels=True ).add_to(hjd) # 행정동 경계 tooltip 으로 행정동명 추가

# layerContrl 추가 
folium.LayerControl().add_to(map)

map


# ### 2) 시간대별 유동인구

# ### 시간대 정의 
# 
# 2019년 월평균 유동인구를 시간대별로 합산하여 2019년 12개월의 시간대별 유동인구 합계를 구하여, 이를 시간대별 통상 유동인구로 가정함.  
# 
# |시간대|시간 범위|시간|
# |---|---|---|
# |새벽|04~07시|3시간|
# |아침|07~09시|2시간|
# |오전|09~12시|3시간|
# |오후|12~18시|6시간|
# |저녁|18~20시|2시간|
# |밤|20~04시|7시간|
# 

# In[68]:


## 혼잡시간대 격자 수 

peak_time_count = ssgi_geo_data.groupby('혼잡시간대').count()
peak_time_count = peak_time_count.reset_index()
peak_time_count = peak_time_count[['혼잡시간대', 'gid']]
peak_time_count = peak_time_count.rename({'gid': '격자 수'}, axis=1)
peak_time_count


# 오후에 유동인구가 많은 지역이 압도적으로 많음

# In[161]:




# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')

# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson"
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8"))
folium.GeoJson(geo_hjd, name='hjg').add_to(map)

yd_ingu = folium.GeoJson(ssgi_geo_data, name='yd_ingu').add_to(map)
folium.features.GeoJsonTooltip(fields=['gid', '새벽' , '아침', '오전', '오후','저녁', '밤', '혼잡시간대'], labels=True ).add_to(yd_ingu)

# 새벽(04~07시) 유동인구
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='04~07_yd_ingu',
        data=ssgi_geo_data,
        columns=['gid', '새벽'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        show= False,
        legend_name='04~07_yd_ingu'
    ).add_to(map)


# 아침(07~09시) 유동인구
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='07~09_yd_ingu',
        data=ssgi_geo_data,
        columns=['gid', '아침'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        show= False,
        legend_name='07~09_yd_ingu'
    ).add_to(map)


# 오전(09~12시) 유동인구
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='09~12_yd_ingu',
        data=ssgi_geo_data,
        columns=['gid', '오전'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        show= False,
        legend_name='09~12_yd_ingu'
    ).add_to(map)

# 오후(12~18시) 유동인구
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='12~18_yd_ingu',
        data=ssgi_geo_data,
        columns=['gid', '오후'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        show= False,
        legend_name='12~18_yd_ingu'
    ).add_to(map)

# 저녁(18~20시) 유동인구
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='18~20_yd_ingu',
        data=ssgi_geo_data,
        columns=['gid', '저녁'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        show= False,
        legend_name='18~20_yd_ingu'
    ).add_to(map)

# 밤(20~04시) 유동인구
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='20~04_yd_ingu',
        data=ssgi_geo_data,
        columns=['gid', '밤'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        show= False,
        legend_name='20~04_yd_ingu'
    ).add_to(map)



folium.LayerControl().add_to(map)

map


# ### 3) 연령대별 카드 이용 비율

# ### 카드_주연령대 살펴보기
# 
# 격자별 카드사용자의 연령대별 비중 중 가장 비중이 큰 연령대를 격자별 소비 주 연령대로 가정함.  
# 지역별 소비의 주연령대를 알아보고 소비 주연령대에 맞는 창업을 제안함.

# In[73]:


## 카드_주연령대 격자 수 

card_age_count = ssgi_geo_data.groupby('카드_주연령대').count()
card_age_count = card_age_count.reset_index()
card_age_count = card_age_count[['카드_주연령대', 'gid']]
card_age_count = card_age_count.rename({'gid': '격자 수'}, axis=1)
card_age_count


# 40대가 주연령대인 격자가 가장 많음.   
# 주 소비 연령대가 40대인 지역이 많음.

# In[ ]:




# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')

# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson"
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8"))
folium.GeoJson(geo_hjd, name='hjg').add_to(map)

card_ratio = folium.GeoJson(ssgi_geo_data, name='card_ratio').add_to(map)
folium.features.GeoJsonTooltip(fields=['gid', '20대' , '30대', '40대', '50대','60대', '70대 이상','카드_주연령대'], labels=True ).add_to(card_ratio)

# 20대 카드이용비율
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='age20_ratio',
        data=ssgi_geo_data,
        columns=['gid', '20대'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        # bins=[0, 25, 50, 75, 100],
        show= False,
        legend_name='age20_ratio (%)'
    ).add_to(map)


# 30대 카드이용비율
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='age30_ratio',
        data=ssgi_geo_data,
        columns=['gid', '30대'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        # bins=[0, 25, 50, 75, 100],
        show= False,
        legend_name='age30_ratio (%)'
    ).add_to(map)


# 40대 카드이용비율
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='age40_ratio',
        data=ssgi_geo_data,
        columns=['gid', '40대'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        # bins=[0, 25, 50, 75, 100],
        show= False,
        legend_name='age40_ratio (%)'
    ).add_to(map)

# 50대 카드이용비율
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='age50_ratio',
        data=ssgi_geo_data,
        columns=['gid', '50대'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        # bins=[0, 25, 50, 75, 100],
        show= False,
        legend_name='age50_ratio (%)'
    ).add_to(map)

# 60대 카드이용비율
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='age60_ratio',
        data=ssgi_geo_data,
        columns=['gid', '60대'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        # bins=[0, 25, 50, 75, 100],
        show= False,
        legend_name='age60_ratio (%)'
    ).add_to(map)

# 70대 이상 카드이용비율
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='age70_ratio',
        data=ssgi_geo_data,
        columns=['gid', '70대 이상'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.6,
        nan_fill_opacity= 0.1,
        line_opacity=0.1,
        # bins=[0, 25, 50, 75, 100],
        show= False,
        legend_name='age70_ratio (%)'
    ).add_to(map)



folium.LayerControl().add_to(map)

map


# ### 4) 혼잡시간대 + 카드 주연령대
# 
# 
# 혼잡시간대 가장 많은 소비가 발생한다고 가정하여 혼잡시간대별로 어떤 연령대가 소비를 가장 많이 하는지 살펴봄.  
# 격자별 소비 주연령대와 혼잡시간대를 결합하여, 그 격자 수를 집계함

# In[78]:


## 혼잡시간대 + 카드이용객의 주연령대 격자 수 

peak_time_card_age_count = ssgi_geo_data.groupby('혼잡시간대_카드_주연령대').count()
peak_time_card_age_count = peak_time_card_age_count.reset_index()
peak_time_card_age_count = peak_time_card_age_count[['혼잡시간대_카드_주연령대', 'gid']]
peak_time_card_age_count = peak_time_card_age_count.rename({'gid': '격자 수'}, axis=1)
peak_time_card_age_count


# 오후에 유동인구가 많은 지역이 가장 많았으며, 소비 주 연령대가 40대인 지역이 가장 많았음.   
# 따라서 '혼잡시간대+카드 주연령대'가 '오후-40대'인 지역이 가장 많음. 오후에 40대의 소비가 가장 많이 발생함.  
# '밤'시간대에 발생하는 소비는 40대에 의한 소비가 가장 많음.  
# '새벽', '아침', '오전'은 유동인구는 있으나 카드 소비가 발생하지 않은 지역이 전부임.

# In[80]:


ssgi_geo_data.columns


# In[106]:




# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')

# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson"
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8"))
folium.GeoJson(geo_hjd, name='hjg').add_to(map)





# 혼잡시간대-40대 추가
style_function3 = lambda x: {'fillColor': 'red' if  x['properties']['혼잡시간대_카드_주연령대'] =='밤 - 40대'
                             else ('blue' if x['properties']['혼잡시간대_카드_주연령대'] =='오후 - 40대' else 'white')}


peaktime_card_age = folium.GeoJson(ssgi_geo_data2, name='peaktime_card_age',style_function=style_function3).add_to(map)
folium.features.GeoJsonTooltip(fields=['gid', '혼잡시간대_카드_주연령대' ,'밤', '40대'], labels=True ).add_to(peaktime_card_age)


# 지도에 layercontrol 추가
folium.LayerControl().add_to(map)

# 지도 시각화
map


# ### 5) 전년대비 증감률 시각화
# 
# 격자별 전년대비 소상공인 매출 증감률을 통해 매출이 증가하며 상권이 살아나는 지역, 매출이 감소하며 상권이 침체되는 지역을 살펴봄.  
# 동기간 비교를 위해 1~3분기의 매출액을 1년 총 매출액으로 가정함. (2020년 3분기 매출까지 있음)  
# 증감률 = (당해 매출액 -전년도 매출액)/ 전년도 매출액 * 100  

# In[ ]:


# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')

# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson"
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8"))
folium.GeoJson(geo_hjd, name='hjg').add_to(map)

# 2018 소상공인 매출 증감률 격자 올리기
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='sales Increase or decrease rate of 2018 (%)',
        data=ssgi_geo_data,
        columns=['gid', 'sales_est_rate_2018'],
        key_on='properties.gid',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='sales Increase or decrease rate of 2018 (%)'
    ).add_to(map)

# 2018 소상공인 매출 격자 올리기
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='sales amount of 2018',
        data=ssgi_geo_data,
        columns=['gid', 'sales_est_amt_2018'],
        key_on='properties.gid',
        fill_color='BuPu',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='sales amount of 2018'
    ).add_to(map)


# 2019 소상공인 매출 증감률 격자 올리기
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='sales Increase or decrease rate of 2019 (%)',
        data=ssgi_geo_data,
        columns=['gid', 'sales_est_rate_2019'],
        key_on='properties.gid',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='sales Increase or decrease rate of 2019 (%)'
    ).add_to(map)

# 2019 소상공인 매출 격자 올리기
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='sales amount of 2019',
        data=ssgi_geo_data,
        columns=['gid', 'sales_est_amt_2019'],
        key_on='properties.gid',
        fill_color='BuPu',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='sales amount of 2019'
    ).add_to(map)

# 2020 소상공인 매출 증감률 격자 올리기
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='sales Increase or decrease rate of 2020 (%)',
        data=ssgi_geo_data,
        columns=['gid', 'sales_est_rate_2020'],
        key_on='properties.gid',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='sales Increase or decrease rate of 2020 (%)'
    ).add_to(map)

# 2018 소상공인 매출 격자 올리기
folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='sales amount of 2020',
        data=ssgi_geo_data,
        columns=['gid', 'sales_est_amt_2020'],
        key_on='properties.gid',
        fill_color='BuPu',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='sales amount of 2020'
    ).add_to(map)


folium.LayerControl().add_to(map)

map


# ## 5) 격자내 소상공인 사업체 대표자의 성별 시각화 
# 
# 대표자가 남성이 여성보다 많으면 : 파란색  
# 대표자가 여성이 남성보다 많으면 : 빨간색  

# In[ ]:


# 시각화를 위해 컬럼명 한글로 바꾸기
ssgi_geo_data = ssgi_geo_data.rename({'ws_cnt':'사업체 수', 'rpr_per_gender_m':'대표자 남', 'rpr_per_gender_f': '대표자 여'
                                     , 'smbiz_yn_cnt'?:'t'} ,axis=1)
# 값 비교를 위해 null값 처리
ssgi_geo_data['사업체 수'] = ssgi_geo_data['사업체 수'].apply(lambda x : 0 if str(x) == 'nan' else x)
ssgi_geo_data['대표자 여'] = ssgi_geo_data['대표자 여'].apply(lambda x : 0 if str(x) == 'nan' else x)
ssgi_geo_data['대표자 남'] = ssgi_geo_data['대표자 남'].apply(lambda x : 0 if str(x) == 'nan' else x)


# In[ ]:



# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')




# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson" 
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8")) # 1. 행정동 경계 데이터 불러오기

style_function = lambda x: {'fillColor': '#ffffff', 'fill_opacity' : '0.1', 'weight':'0.8'} # 행정동 경계 스타일
hjd = folium.GeoJson(geo_hjd, name='hjg', style_function=style_function).add_to(map) # 행정동 경계 지도에 추가하기
folium.features.GeoJsonTooltip(fields=['ADM_DR_NM'], labels=True ).add_to(hjd) # 행정동 경계 tooltip 으로 행정동명 추가


# 성별별 대표자 수 추가
style_function2 = lambda x: {'fillColor': 'red' if  x['properties']['대표자 여'] > x['properties']['대표자 남']
                             else ('blue' if x['properties']['대표자 여'] < x['properties']['대표자 남'] else 'white')}


ceo_mf = folium.GeoJson(ssgi_geo_data, name='ceo_m/f',   style_function=style_function2).add_to(map)
folium.features.GeoJsonTooltip(fields=['gid', '사업체 수' , '대표자 남', '대표자 여'], labels=True ).add_to(ceo_mf)
# tooltip에 시간대별 유동인구 및 혼잡시간대 추가


folium.Choropleth(
        geo_data=ssgi_geo_data,
        name='ssgi_cnt',
        data=ssgi_geo_data,
        columns=['gid', '사업체 수'],
        key_on='properties.gid',
        fill_color='OrRd',
        fill_opacity=0.7,
        line_opacity=0.1,
        show=False
        legend_name='sssgi_cnt'
    ).add_to(map)


# folium.features.Vega(yd_peak_card_age4, width=None, height=None, left='0%', top='0%', position='relative').add_to(yd_ingu)

# 지도에 layercontrol 추가
folium.LayerControl().add_to(map)

# 지도 시각화
map


# ### MarkerCluster를 이용한 소상공인 현황 시각화

# In[ ]:


# 용인시_상권정보_gid 불러오기
sg_data = pd.read_csv('./input/1.용인시_상권_정보.csv', encoding='utf-8')
sg_data.head()


# In[ ]:


from folium.plugins import MarkerCluster

# 지도 객체 생성
yongin_center = [37.233333, 127.2]
map = folium.Map(location=yongin_center, zoom_start=11,
                tiles='http://api.vworld.kr/req/wmts/1.0.0/47406BFB-8650-3762-B149-F47955A2B559/Base/{z}/{y}/{x}.png',
               attr='용인시')

# 행정동 경계 추가
geo_path_hjd ="./input/13.용인시_행정경계(읍면동).geojson"
geo_hjd = json.load(open(geo_path_hjd, encoding="utf-8"))
folium.GeoJson(geo_hjd, name='hjg').add_to(map)

marker_cluster = MarkerCluster().add_to(map) # create marker clusters

for n in range(sg_data.shape[0]):
    location = [sg_data["위도"][n],sg_data["경도"][n]]
    tooltip = "gb_nm:{}<br> address: {}".format(sg_data["표준산업분류명"][n], sg_data['도로명주소'][n])
    folium.Marker(location, icon=folium.Icon(icon="check",color="lightblue"), tooltip = tooltip).add_to(marker_cluster)




map


# In[ ]:





# In[ ]:




