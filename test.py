import pandas as pd

path = r'/data1/fyliu/f_rainfall_varaibility_daily_monthly/data/mean_trend/2000_2020_gte15/station_isd.csv'
df = pd.read_csv(path)
duplicates = df[df.duplicated(subset=['lon', 'lat'], keep=False)]

if not duplicates.empty:
    print('duplicates:')
    duplicate_counts = duplicates.groupby(['lon', 'lat']).size().reset_index(name='count')
    print(duplicate_counts)
else:
    print('NO duplicates')
