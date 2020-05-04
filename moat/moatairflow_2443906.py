

# In[1]:


import urllib3
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
import json
import pandas as pd
from pandas import json_normalize
import logging
import numpy as np
import sys
from io import StringIO # if going with no saving csv file
from io import BytesIO
import pyarrow



## GOOGLE CLOUD libraries 
from googleapiclient import discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import storage
import gcsfs

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# In[2]:


### DEFINING TIME PARAMETERS

yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
pastweek= ((date.today() - timedelta(days=1)) - timedelta(weeks=1)).strftime('%Y-%m-%d')
threedays= ((date.today() - timedelta(days=1)) - timedelta(days=4)).strftime('%Y-%m-%d')

logging.info(f'ETL job starts, Libraries have been imported successfully: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')



### DEFINING BIGQUERY PARAMETERS

project_id = "essence-analytics-libra" 
dataset_id = "moatapac"
short_table_name = 'Essence_Google_YouTube_Trueview_APAC' # this is used when table name is fed to BQ query (time check)
bq_table_id = f'{project_id}.{dataset_id}.{short_table_name}' # this is used when table is fed to the BQ data load job

logging.info(f'BIGQUERY parameters have been created SUCCESSFULLY: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')



### DEFINING CLOUD STORAGE PARAMETERS

bucket_name = 'moat_apac_essence'
bucket_path = 'gs://moat_apac_essence'
bucket_object = f'{short_table_name}/{short_table_name}_{date.today()-timedelta(days=1)}.csv'


# In[8]:


### DEFINING MOAT PARAMETERS

table_id = 2443906
moat_token = 'cTbOcDEJPPxoD6oQySLAUqxh1n7gH32y6qTdGNJw' ## MOAT Token 
moat_variables = ('date','level1' ,'level2','level3','level4','loads_unfiltered','loads_git','impressions_analyzed',
                  'l_perc','susp_human','susp_human_perc','susp_human_and_inview_meas_sum','susp_human_and_inview_meas_perc',
                  'human_and_viewable','human_and_viewable_perc','human_and_inview_3sec_cumulative','human_and_inview_3sec_cumulative_perc',
                  'susp_human_and_inview_gm_meas_sum','susp_human_and_inview_gm_meas_perc','human_and_avoc',
                  'human_and_avoc_perc','human_and_viewable_gm_video','human_and_viewable_gm_video_perc',
                  'human_and_viewable_gm_video_15cap_sum','human_and_viewable_gm_video_15cap_perc',
                  'human_and_groupm_video_ots_completion','human_and_groupm_video_ots_completion_perc',
                  'susp_l_measurable_perc','susp_bot_perc','susp_bot_data_center_perc','susp_bot_spider_perc',
                  'susp_bot_proxy_perc','susp_bot_browser_perc','susp_bot_geo_perc','susp_bot_susp_browser_perc',
                  'susp_late_night_perc','susp_old_browser_perc','susp_top_hour_perc','susp_ms_abf_perc',
                  'strict_or_px_2sec_consec_video_ots_unfiltered','strict_or_px_2sec_consec_video_ots_git',
                  'in_view_measurable_unfiltered_percent',
                  'in_view_measurable_git_percent','in_view_measurable_percent','om_sdk_measurable_imps',
                  'om_sdk_measurable_rate','swf_img_loads','l_mobile','l_mobile_not_iframe','scroll_measurable_impressions',
                  'l_somehow_measurable_unfiltered','l_somehow_measurable_git','measurable_impressions',
                  '1_sec_in_view_impressions','video_2_sec_consecutive_visible_unfiltered_percent',
                  'video_2_sec_consecutive_visible_git_percent',
                  '2_sec_video_in_view_impressions','inview_3sec_cumulative','5_sec_in_view_impressions',
                  '1_sec_video_in_view_percent','2_sec_video_in_view_percent','inview_3sec_cumulative_perc',
                  '5_sec_video_in_view_percent','l_full_visibility_measurable','l_full_visibility_ots_1_sec',
                  'l_full_visibility_ots_1_sec_percent','fully_on_screen_2_continuous_seconds_publicis_video_imps',
                  'fully_on_screen_2_continuous_seconds_publicis_video_pct','fully_on_screen_3sec_cumulative',
                  'fully_on_screen_3sec_cumulative_perc','ad_duration','percent_of_airtime_visible','video_in_view_time',
                  'video_exposure_time','average_minute_audience','reached_first_quart_sum','reached_first_quart_percent',
                  'reached_second_quart_sum','reached_second_quart_percent','reached_third_quart_sum','reached_third_quart_percent',
                  'reached_complete_sum','reached_complete_percent','player_audible_on_first_quart_percent',
                  'player_audible_on_second_quart_percent','player_audible_on_third_quart_percent',
                  'player_audible_on_complete_percent','player_visible_on_first_quart_percent',
                  'player_visible_on_second_quart_percent','player_visible_on_third_quart_percent',
                  'player_visible_on_complete_percent','player_audible_on_first_quart_sum',
                  'player_audible_on_second_quart_sum','player_audible_on_third_quart_sum','player_audible_on_complete_sum',
                  'player_visible_on_first_quart_sum','player_visible_on_second_quart_sum',
                  'player_visible_on_third_quart_sum','player_visible_on_complete_sum','player_vis_and_aud_on_start_sum',
                  'player_vis_and_aud_on_start_percent','player_vis_and_aud_on_first_quart_sum',
                  'ad_vis_and_aud_on_first_quart_percent','player_vis_and_aud_on_second_quart_sum',
                  'ad_vis_and_aud_on_second_quart_percent','player_vis_and_aud_on_third_quart_sum','ad_vis_and_aud_on_third_quart_percent',
                  'player_vis_and_aud_on_complete_sum','ad_vis_and_aud_on_complete_percent','player_audible_full_vis_half_time_sum',
                  'player_audible_full_vis_half_time_percent','viewable_gm_video_15cap_sum',
                  'viewable_gm_video_15cap_perc','groupm_video_ots_completion','groupm_video_ots_completion_perc',
                  'yt_tv_groupm_measurable','yt_tv_groupm_measurable_perc','yt_tv_groupm_viewable','yt_tv_groupm_viewable_perc',
                  'mrc_2_sec_and_complete','mrc_2_sec_and_complete_perc','completion_quality')



moat_metrics =['human_and_inview_3sec_cumulative_perc',
                  'susp_human_and_inview_gm_meas_sum','susp_human_and_inview_gm_meas_perc','human_and_avoc',
                  'human_and_avoc_perc','human_and_viewable_gm_video','human_and_viewable_gm_video_perc',
                  'human_and_viewable_gm_video_15cap_sum','human_and_viewable_gm_video_15cap_perc',
                  'human_and_groupm_video_ots_completion','human_and_groupm_video_ots_completion_perc',
                  'susp_l_measurable_perc','susp_bot_perc','susp_bot_data_center_perc','susp_bot_spider_perc',
                  'susp_bot_proxy_perc','susp_bot_browser_perc','susp_bot_geo_perc','susp_bot_susp_browser_perc',
                  'susp_late_night_perc','susp_old_browser_perc','susp_top_hour_perc','susp_ms_abf_perc',
                  'strict_or_px_2sec_consec_video_ots_unfiltered','strict_or_px_2sec_consec_video_ots_git',
                  'in_view_measurable_unfiltered_percent','in_view_measurable_git_percent','in_view_measurable_percent',
                  'om_sdk_measurable_imps','om_sdk_measurable_rate','swf_img_loads','l_mobile','l_mobile_not_iframe',
                  'scroll_measurable_impressions','l_somehow_measurable_unfiltered','l_somehow_measurable_git',
                  'measurable_impressions','1_sec_in_view_impressions','video_2_sec_consecutive_visible_unfiltered_percent',
                  'video_2_sec_consecutive_visible_git_percent','2_sec_video_in_view_impressions','inview_3sec_cumulative',
                  '5_sec_in_view_impressions','1_sec_video_in_view_percent','2_sec_video_in_view_percent','inview_3sec_cumulative_perc',
                  '5_sec_video_in_view_percent','l_full_visibility_measurable','l_full_visibility_ots_1_sec',
                  'l_full_visibility_ots_1_sec_percent',
                  'fully_on_screen_2_continuous_seconds_publicis_video_imps','fully_on_screen_2_continuous_seconds_publicis_video_pct',
                  'fully_on_screen_3sec_cumulative','fully_on_screen_3sec_cumulative_perc','ad_duration',
                  'percent_of_airtime_visible','video_in_view_time','video_exposure_time','average_minute_audience',
                  'reached_first_quart_sum','reached_first_quart_percent','reached_second_quart_sum',
                  'reached_second_quart_percent','reached_third_quart_sum','reached_third_quart_percent',
                  'reached_complete_sum','reached_complete_percent','player_audible_on_first_quart_percent',
                  'player_audible_on_second_quart_percent','player_audible_on_third_quart_percent',
                  'player_audible_on_complete_percent','player_visible_on_first_quart_percent',
                  'player_visible_on_second_quart_percent','player_visible_on_third_quart_percent','player_visible_on_complete_percent',
                  'player_audible_on_first_quart_sum','player_audible_on_second_quart_sum','player_audible_on_third_quart_sum',
                  'player_audible_on_complete_sum','player_visible_on_first_quart_sum','player_visible_on_second_quart_sum',
                  'player_visible_on_third_quart_sum','player_visible_on_complete_sum','player_vis_and_aud_on_start_sum',
                  'player_vis_and_aud_on_start_percent','player_vis_and_aud_on_first_quart_sum','ad_vis_and_aud_on_first_quart_percent',
                  'player_vis_and_aud_on_second_quart_sum','ad_vis_and_aud_on_second_quart_percent',
                  'player_vis_and_aud_on_third_quart_sum','ad_vis_and_aud_on_third_quart_percent',
                  'player_vis_and_aud_on_complete_sum','ad_vis_and_aud_on_complete_percent',
                  'player_audible_full_vis_half_time_sum','player_audible_full_vis_half_time_percent',
                  'viewable_gm_video_15cap_sum','viewable_gm_video_15cap_perc','groupm_video_ots_completion',
                  'groupm_video_ots_completion_perc','yt_tv_groupm_measurable','yt_tv_groupm_measurable_perc','yt_tv_groupm_viewable',
                  'yt_tv_groupm_viewable_perc','mrc_2_sec_and_complete','mrc_2_sec_and_complete_perc','completion_quality']


moat_query = {
  'brandId': table_id,
  'metrics': ','.join(moat_variables),
  'start':pastweek,
  'end': yesterday
            }

bq_schema = [bigquery.SchemaField('Date', 'DATE', mode="Nullable"),
             bigquery.SchemaField('Advertiser_ID', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Advertiser_Name', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Campaign_ID', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Campaign_Name', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Line_Item_ID', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Line_Item_Name', 'STRING', mode="Nullable"),                         
             bigquery.SchemaField('Creative_ID', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Creative_Name', 'STRING', mode="Nullable"),
             bigquery.SchemaField('Impressions_Analyzed_unfiltered', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Impressions_Analyzed_filtered_for_GIVT', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Impressions_Analyzed', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Percentage_of_Total_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_InView_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_InView_Measurable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_Viewable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_Viewable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_3_Sec_InView_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_3_Sec_InView_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_Fully_OnScreen_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_Fully_OnScreen_Measurable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_AVOC_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_And_AVOC_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('IVT_Measurable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('IVT_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Data_Center_Traffic_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Spider_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Invalid_Proxy_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Automated_Browser_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('NonUS_Traffic_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Incongruous_Browser_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Late_Night_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Outdated_Browser_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Top_of_the_Hour_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Excessive_Activity_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_InView_Impressions_unfiltered', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_InView_Impressions_filtered_for_GIVT', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Measurable_Rate_unfiltered', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Measurable_Rate_filtered_for_GIVT', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Measurable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('OM_SDK_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('OM_SDK_Measurable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('SWF_IMG_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Mobile_Impressions_Analyzed', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Mobile_NonIframe_Impressions_Analyzed', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Scroll_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Measurable_Impressions_unfiltered', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Measurable_Impressions_filtered_for_GIVT', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('One_Sec_InView_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_Video_InView_Rate_unfiltered', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_Video_InView_Rate_filtered_for_GIVT', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_InView_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Three_Sec_InView_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Five_Sec_InView_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('One_Sec_Video_InView_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_Video_InView_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Three_Sec_Video_InView_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Five_Sec_Video_InView_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Fully_OnScreen_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('One_Sec_Fully_OnScreen_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('One_Sec_Fully_OnScreen_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_Fully_OnScreen_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_Fully_OnScreen_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Three_Sec_Fully_OnScreen_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Three_Sec_Fully_OnScreen_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Averaged_Ad_Length', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Perc_of_Video_Played_InView', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('InView_Time', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Total_Exposure_Time_hr', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Average_Minute_Audience', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_1st_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_1st_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_2nd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_2nd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_3rd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_3rd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_Complete_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Reached_Complete_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_1st_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_2nd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_3rd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_Complete_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_1st_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_2nd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_3rd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_Completion_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_1st_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_2nd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_3rd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_On_Complete_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_1st_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_2nd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_3rd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Visible_On_Completion_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_on_Start_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_on_Start_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_at_1st_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_at_1st_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_at_2nd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_at_2nd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_at_3rd_Quartile_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_at_3rd_Quartile_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_on_Complete_Sum', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Visible_on_Complete_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Measurable_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Measurable_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_InView_And_Reached_Completion_Impressions', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Two_Sec_InView_And_Reached_Completion_Rate', 'FLOAT', mode='Nullable'),
             bigquery.SchemaField('Completion_Quality', 'FLOAT', mode='Nullable'),
]

logging.info(f'MOAT parameters have been created SUCCESSFULLY: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


# In[9]:


#### THIS IS TO SAVE MOAT API RESPONSE

def df_to_bucket(bucket_name, bucket_object, source_file_name):  
    """Uploads a file to the bucket."""
    storage_cred = service_account.Credentials.from_service_account_file('libra.json')
    storage_client = storage.Client(credentials = storage_cred, project='essence-analytics-libra')
    
    f = StringIO()
    df.to_csv(f, index=False)
    f.seek(0)

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(bucket_object)
    
    blob.upload_from_file(f, content_type='text/csv')
    print(f'CSV has been UPLOADED TO BUCKET: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logging.info(f'CSV has been UPLOADED TO BUCKET: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

### MOAT API CALL
def moat_stat_request(token, metrics, query, brandid):  ####
    auth_header = 'Bearer {}'.format(moat_token)
    http = urllib3.PoolManager()
    #http = urllib3.HTTPSConnectionPool('api.moat.com', port=443, cert_reqs='CERT_NONE', assert_hostname=False)
    resp1 = http.request('GET', 'https://api.moat.com/1/stats.json',fields=moat_query,headers={'Authorization': auth_header})
    raw_data = json.loads(resp1.data.decode('utf-8'))
    df = pd.json_normalize(raw_data['results']['details']) # max_level=1
    return df

### MOAT COLUMN RENAMING FUNCTION


def column_renaming(df):
    df.rename(columns={'date': 'Date',
                       'level1_id': 'Advertiser_ID', 'level1_label': 'Advertiser_Name',
                       'level2_id': 'Campaign_ID', 'level2_label': 'Campaign_Name',
                       'level3_id': 'Line_Item_ID', 'level3_label': 'Line_Item_Name',
                       'level4_id': 'Creative_ID', 'level4_label': 'Creative_Name',
                       'loads_unfiltered':'Impressions_Analyzed_unfiltered',
                       'loads_git':'Impressions_Analyzed_filtered_for_GIVT',
                       'impressions_analyzed':'Impressions_Analyzed',
                       'l_perc':'Percentage_of_Total_Impressions',
                       'susp_human':'Valid_Impressions',
                       'susp_human_perc':'Valid_Rate',
                       'susp_human_and_inview_meas_sum':'Valid_And_InView_Measurable_Impressions',
                       'susp_human_and_inview_meas_perc':'Valid_And_InView_Measurable_Rate',
                       'human_and_viewable':'Valid_And_Viewable_Impressions',
                       'human_and_viewable_perc':'Valid_And_Viewable_Rate',
                       'human_and_inview_3sec_cumulative':'Valid_And_3_Sec_InView_Impressions',
                       'human_and_inview_3sec_cumulative_perc':'Valid_And_3_Sec_InView_Rate',
                       'susp_human_and_inview_gm_meas_sum':'Valid_And_Fully_OnScreen_Measurable_Impressions',
                       'susp_human_and_inview_gm_meas_perc':'Valid_And_Fully_OnScreen_Measurable_Rate',
                       'human_and_avoc':'Valid_And_AVOC_Impressions',
                       'human_and_avoc_perc':'Valid_And_AVOC_Rate',
                       'human_and_viewable_gm_video':'Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_Impressions',
                       'human_and_viewable_gm_video_perc':'Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_Rate',
                       'human_and_viewable_gm_video_15cap_sum':'Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Impressions',
                       'human_and_viewable_gm_video_15cap_perc':'Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Rate',
                       'human_and_groupm_video_ots_completion':'Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Impressions',
                       'human_and_groupm_video_ots_completion_perc':'Valid_Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Rate',
                       'susp_l_measurable_perc':'IVT_Measurable_Rate',
                       'susp_bot_perc':'IVT_Rate',
                       'susp_bot_data_center_perc':'Data_Center_Traffic_Rate',
                       'susp_bot_spider_perc':'Spider_Rate',
                       'susp_bot_proxy_perc':'Invalid_Proxy_Rate',
                       'susp_bot_browser_perc':'Automated_Browser_Rate',
                       'susp_bot_geo_perc':'NonUS_Traffic_Rate',
                       'susp_bot_susp_browser_perc':'Incongruous_Browser_Rate',
                       'susp_late_night_perc':'Late_Night_Rate',
                       'susp_old_browser_perc':'Outdated_Browser_Rate',
                       'susp_top_hour_perc':'Top_of_the_Hour_Rate',
                       'susp_ms_abf_perc':'Excessive_Activity_Rate',
                       'strict_or_px_2sec_consec_video_ots_unfiltered':'Two_Sec_InView_Impressions_unfiltered',
                       'strict_or_px_2sec_consec_video_ots_git':'Two_Sec_InView_Impressions_filtered_for_GIVT',
                       'in_view_measurable_unfiltered_percent':'InView_Measurable_Rate_unfiltered',
                       'in_view_measurable_git_percent':'InView_Measurable_Rate_filtered_for_GIVT',
                       'in_view_measurable_percent':'InView_Measurable_Rate',
                       'om_sdk_measurable_imps':'OM_SDK_Measurable_Impressions',
                       'om_sdk_measurable_rate':'OM_SDK_Measurable_Rate',
                       'swf_img_loads':'SWF_IMG_Impressions',
                       'l_mobile':'Mobile_Impressions_Analyzed',
                       'l_mobile_not_iframe':'Mobile_NonIframe_Impressions_Analyzed',
                       'scroll_measurable_impressions':'Scroll_Measurable_Impressions',
                       'l_somehow_measurable_unfiltered':'InView_Measurable_Impressions_unfiltered',
                       'l_somehow_measurable_git':'InView_Measurable_Impressions_filtered_for_GIVT',
                       'measurable_impressions':'InView_Measurable_Impressions',
                       '1_sec_in_view_impressions':'One_Sec_InView_Impressions',
                       'video_Two_sec_consecutive_visible_unfiltered_percent':'Two_Sec_Video_InView_Rate_unfiltered',
                       'video_Two_sec_consecutive_visible_git_percent':'Two_Sec_Video_InView_Rate_filtered_for_GIVT',
                       '2_sec_video_in_view_impressions':'Two_Sec_InView_Impressions',
                       'inview_3sec_cumulative':'Three_Sec_InView_Impressions',
                       '5_sec_in_view_impressions':'Five_Sec_InView_Impressions',
                       '1_sec_video_in_view_percent':'One_Sec_Video_InView_Rate',
                       '2_sec_video_in_view_percent':'Two_Sec_Video_InView_Rate',
                       'inview_3sec_cumulative_perc':'Three_Sec_Video_InView_Rate',
                       '5_sec_video_in_view_percent':'Five_Sec_Video_InView_Rate',
                       'l_full_visibility_measurable':'Fully_OnScreen_Measurable_Impressions',
                       'l_full_visibility_ots_1_sec':'One_Sec_Fully_OnScreen_Impressions',
                       'l_full_visibility_ots_1_sec_percent':'One_Sec_Fully_OnScreen_Rate',
                       'fully_on_screen_2_continuous_seconds_publicis_video_imps':'Two_Sec_Fully_OnScreen_Impressions',
                       'fully_on_screen_2_continuous_seconds_publicis_video_pct':'Two_Sec_Fully_OnScreen_Rate',
                       'fully_on_screen_3sec_cumulative':'Three_Sec_Fully_OnScreen_Impressions',
                       'fully_on_screen_3sec_cumulative_perc':'Three_Sec_Fully_OnScreen_Rate',
                       'ad_duration':'Averaged_Ad_Length',
                       'percent_of_airtime_visible':'Perc_of_Video_Played_InView',
                       'video_in_view_time':'InView_Time',
                       'video_exposure_time':'Total_Exposure_Time_hr',
                       'average_minute_audience':'Average_Minute_Audience',
                       'reached_first_quart_sum':'Reached_1st_Quartile_Sum',
                       'reached_first_quart_percent':'Reached_1st_Quartile_Rate',
                       'reached_second_quart_sum':'Reached_2nd_Quartile_Sum',
                       'reached_second_quart_percent':'Reached_2nd_Quartile_Rate',
                       'reached_third_quart_sum':'Reached_3rd_Quartile_Sum',
                       'reached_third_quart_percent':'Reached_3rd_Quartile_Rate',
                       'reached_complete_sum':'Reached_Complete_Sum',
                       'reached_complete_percent':'Reached_Complete_Rate',
                       'player_audible_on_first_quart_percent':'Audible_On_1st_Quartile_Rate',
                       'player_audible_on_second_quart_percent':'Audible_On_2nd_Quartile_Rate',
                       'player_audible_on_third_quart_percent':'Audible_On_3rd_Quartile_Rate',
                       'player_audible_on_complete_percent':'Audible_On_Complete_Rate',
                       'player_visible_on_first_quart_percent':'Visible_On_1st_Quartile_Rate',
                       'player_visible_on_second_quart_percent':'Visible_On_2nd_Quartile_Rate',
                       'player_visible_on_third_quart_percent':'Visible_On_3rd_Quartile_Rate',
                       'player_visible_on_complete_percent':'Visible_On_Completion_Rate',
                       'player_audible_on_first_quart_sum':'Audible_On_1st_Quartile_Sum',
                       'player_audible_on_second_quart_sum':'Audible_On_2nd_Quartile_Sum',
                       'player_audible_on_third_quart_sum':'Audible_On_3rd_Quartile_Sum',
                       'player_audible_on_complete_sum':'Audible_On_Complete_Sum',
                       'player_visible_on_first_quart_sum':'Visible_On_1st_Quartile_Sum',
                       'player_visible_on_second_quart_sum':'Visible_On_2nd_Quartile_Sum',
                       'player_visible_on_third_quart_sum':'Visible_On_3rd_Quartile_Sum',
                       'player_visible_on_complete_sum':'Visible_On_Completion_Sum',
                       'player_vis_and_aud_on_start_sum':'Audible_And_Visible_on_Start_Sum',
                       'player_vis_and_aud_on_start_percent':'Audible_And_Visible_on_Start_Rate',
                       'player_vis_and_aud_on_first_quart_sum':'Audible_And_Visible_at_1st_Quartile_Sum',
                       'ad_vis_and_aud_on_first_quart_percent':'Audible_And_Visible_at_1st_Quartile_Rate',
                       'player_vis_and_aud_on_second_quart_sum':'Audible_And_Visible_at_2nd_Quartile_Sum',
                       'ad_vis_and_aud_on_second_quart_percent':'Audible_And_Visible_at_2nd_Quartile_Rate',
                       'player_vis_and_aud_on_third_quart_sum':'Audible_And_Visible_at_3rd_Quartile_Sum',
                       'ad_vis_and_aud_on_third_quart_percent':'Audible_And_Visible_at_3rd_Quartile_Rate',
                       'player_vis_and_aud_on_complete_sum':'Audible_And_Visible_on_Complete_Sum',
                       'ad_vis_and_aud_on_complete_percent':'Audible_And_Visible_on_Complete_Rate',
                       'player_audible_full_vis_half_time_sum':'Audible_And_Fully_OnScreen_for_Half_of_Duration_Impressions',
                       'player_audible_full_vis_half_time_percent':'Audible_And_Fully_OnScreen_for_Half_of_Duration_Rate',
                       'viewable_gm_video_15cap_sum':'Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Impressions',
                       'viewable_gm_video_15cap_perc':'Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_Rate',
                       'groupm_video_ots_completion':'Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Impressions',
                       'groupm_video_ots_completion_perc':'Audible_And_Fully_OnScreen_for_Half_of_Duration_15_sec_cap_with_Completion_Rate',
                       'yt_tv_groupm_measurable':'Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Measurable_Impressions',
                       'yt_tv_groupm_measurable_perc':'Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Measurable_Rate',
                       'yt_tv_groupm_viewable':'Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Impressions',
                       'yt_tv_groupm_viewable_perc':'Audible_And_Fully_OnScreen_for_Half_of_Duration_TrueView_Rate',
                       'mrc_2_sec_and_complete':'Two_Sec_InView_And_Reached_Completion_Impressions',
                       'mrc_2_sec_and_complete_perc':'Two_Sec_InView_And_Reached_Completion_Rate',
                       'completion_quality':'Completion_Quality'}, inplace=True)


def table_name_change(mainString, toBeReplaces, newString):
    # Iterate over the strings to be replaced
    for elem in toBeReplaces :
        # Check if string is in the main string
        if elem in mainString :
            # Replace the string
            mainString = mainString.replace(elem, newString)
    return  mainString


### THIS IS TO READ CSV FROM STORAGE AND LOAD IT TO BQ

# THIS ONE IS TEST, not to keep
def csv_to_bq():
    cred = service_account.Credentials.from_service_account_file('libra.json')
    bq_client = bigquery.Client(credentials = cred, project = 'essence-analytics-libra')
    
    dataset_ref = bq_client.dataset(dataset_id)
    job_config = bigquery.LoadJobConfig()
    job_config.autodetect = True
    job_config.source_format = bigquery.SourceFormat.CSV #NEWLINE_DELIMITED_JSON
    uri = "gs://cloud-samples-data/bigquery/us-states/us-states.json"
    load_job = client.load_table_from_uri(
        uri, dataset_ref.table("us_states"), job_config=job_config
    )  # API request
    print("Starting job {}".format(load_job.job_id))

    load_job.result()  # Waits for table load to complete.
    print("Job finished.")

    destination_table = client.get_table(dataset_ref.table("us_states"))
    print("Loaded {} rows.".format(destination_table.num_rows))



## FINAL FUNCTION FOR BQ LOAD -this is to keep    
### function to process file in chunks

def process(nums=moat_metrics): #cols=cols, schema=schema

    path = f'{short_table_name}/{short_table_name}_{date.today()-timedelta(days=1)}.csv'
    storage_cred = service_account.Credentials.from_service_account_file('libra.json')
    storage_client = storage.Client(credentials = storage_cred, project=project_id)

    bucket = storage_client.get_bucket(bucket_name)
    blob = storage.Blob(path, bucket)
    content = blob.download_as_string()

    df = pd.read_csv(BytesIO(content), encoding='latin1')
    
    for v in nums:
        # coerce numerical columns to floats
        df[v] = df[v].replace(r'^\s*$', np.nan, regex=True)
        df[v] = df[v].apply(pd.to_numeric,errors='coerce')
        df[v] = df[v].astype(float)

    column_renaming(df)
    df['Date'] = pd.to_datetime(df['Date'],format='%Y-%m-%d',errors='coerce')
    df = df.drop(columns=['susp_valid_and_inview_gm_meas_sum','susp_valid_and_inview_gm_meas_perc',
                                        'valid_and_viewable_gm_video','valid_and_viewable_gm_video_perc',
                                        'valid_and_viewable_gm_video_15cap_sum','valid_and_viewable_gm_video_15cap_perc',
                                        'valid_and_avoc','valid_and_avoc_perc','valid_and_inview_3sec_cumulative_perc',
                                        'valid_and_groupm_video_ots_completion','valid_and_groupm_video_ots_completion_perc'])
    df.set_index('Date',inplace=True)

    #####################
    #
    # THIS PART LOADS DF TO BQ TABLE
    #
    #####################
    
    cred = service_account.Credentials.from_service_account_file('libra.json')
    bq_client = bigquery.Client(credentials = cred, project = 'essence-analytics-libra')

    logging.info(f'BIGQUERY dataload STARTS: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    job_config = bigquery.LoadJobConfig(schema=bq_schema) #have to define schema   
    job = bq_client.load_table_from_dataframe(df, bq_table_id, job_config=job_config)  # Make an API request.
    job.result()  # Wait for the job to complete.
    table = bigQueryClient.get_table(bq_table_id)  # Make an API request.

    #####################
    #
    # THIS PART CHECKS AND DELETES TIME OVERLAP BETWEEN DF AND BQ TABLE
    #
    #####################

    
    #logging.info(f'Check & DELETE data overlap between new DF and existing BQ table: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    #min_date = df['Date'].min().strftime('%Y-%m-%d')
    #max_date = df['Date'].max().strftime('%Y-%m-%d')

    #bq_query = f"""DELETE FROM `{project_id}.{dataset_id}.{short_table_name}` 
    #           WHERE `Date` BETWEEN '{min_date}' AND '{max_date}';""" 

    #query_job = bq_client.query(bq_query)  # Make an API request. ,job_config=job_config

    #query_job.result()
    #logging.info(f'BIGQUERY job has been executed with QUERY ID: {query_job.job_id}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    


    #####################
    #
    # THIS PART LOADS DF TO BQ TABLE
    #
    #####################


        


# In[ ]:


df = moat_stat_request(moat_token, moat_variables, moat_query, table_id)
print(df.columns)
logging.info(f'df: MOAT dataframe has been created SUCCESSFULLY: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


# In[14]:


df_to_bucket(bucket_name, bucket_object, df)


# In[15]:


process(nums=moat_metrics)


# In[ ]:


print(df.columns)

