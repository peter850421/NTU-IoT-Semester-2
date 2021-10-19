from datetime import datetime, timezone
import hashlib
import io
import re
import time

import matplotlib.pyplot as plt
import matplotlib.dates

from util import query_distance, upload_fileobj, set_user_state

def process_distance(text, id, has_queried_date=False):
    if not has_queried_date:
        set_user_state(id, 'distance')

        return {
            'type': 'text',
            'text': '請輸入日期（e.g., 2020-01-08）或幾分鐘前的資料（e.g., 5分鐘前）：'
        }
    else:
        try:
            if '-' in text:
                year, month, day = text.split('-')
                year = int(year)
                month = int(month)
                day = int(day)
                start_time = int(datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc).timestamp())
                end_time = int(datetime(year, month, day, 23, 59, 59, tzinfo=timezone.utc).timestamp())
            else:
                minutes_before = int(re.sub('[^0-9]','', text))
                start_time = int(time.time()-60*minutes_before)
                end_time = int(time.time())
        except ValueError as e:
            # wrong format
            return {
                'type': 'text',
                'text': '輸入格式不對！請再次輸入日期（e.g., 2020-01-08）或幾分鐘前的資料（e.g., 5分鐘前）：'
            }

        # return a graph that contains lighting information
        # start_time = 1610064000 # GMT 2021-01-08 00:00:00
        # end_time = 1610150399 # GMT 2021-01-08 23:59:59

        # sort by time
        values = query_distance(start_time, end_time)

        # check if there's items in the query
        if len(values) > 0:
            values.sort(key=lambda val: val[0])

            # convert all times to matplotlib format
            times, light_vals = zip(*values)
            times = [matplotlib.dates.date2num(datetime.fromtimestamp(t)) for t in times]

            # plot the graph
            fileobj = io.BytesIO()
            plt.plot_date(times, light_vals, 'b-', tz='Asia/Taipei')
            plt.gcf().autofmt_xdate()
            plt.ylabel('Distance (cm)')
            plt.ylim(0, 750)
            plt.savefig(fileobj, format='png')
            plt.clf()
            fileobj.seek(0)

            # filename pattern: two digit hash of id/id/timestamp
            id_hash = hashlib.sha1(id.encode('utf-8')).hexdigest()[:2]
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())

            object_name = id_hash + '/' + id + '/' + timestamp + '.png'
            url = upload_fileobj(fileobj, 'smarteyes-linebotserver', object_name)
            response = {
                'type': 'image',
                'originalContentUrl': url,
                'previewImageUrl': url
            }
        else:
            response = {
                'type': 'text',
                'text': '這時段沒有資料喔！'
            }

        set_user_state(id, '')

        return response
