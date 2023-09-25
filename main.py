import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import psycopg2
import pandas as pd
from sshtunnel import SSHTunnelForwarder
from datetime import datetime, timedelta


host = '185.20.224.243'
user = 'root'
secret = 'Js3vyA-3~4MA'
port = 22


db_host = 'localhost'
db_port = 5432
db_username = 'testuser'
db_password = 'TEST_PAROL'
db_database = 'er_bot_development'



def get_data(connection, date_start, date_end):
    data = []
    current_time = date_start

    while current_time <= date_end:
        next_time = current_time + timedelta(hours=1) #прибавляется один час

        curs = connection.cursor()
        curs.execute(
            #получаем  количвество юзеров в заданном интервале
            """
            SELECT COUNT(*) 
            FROM users
            WHERE created_at >= %s AND created_at < %s
            """,
            (current_time, next_time)
        )
        count = curs.fetchone()[0] #получ результат запроса

        data.append({'time_interval': current_time, 'object_count': count}) #добавляется в словарь текущее время и количество юзеров

        current_time = next_time

    return data



app = dash.Dash(__name__)


date_start_default = datetime(2023, 9, 1)
date_end_default = datetime(2023, 9, 22)

app.layout = html.Div([
    html.Label('Дата начала:'),
    dcc.DatePickerSingle( #создание виджета для даты
        id='date-start',
        display_format='YYYY-MM-DD',
        date=date_start_default.strftime('%Y-%m-%d'),  # Устанавливает начальное значение выбранной даты
        disabled=True  # Запрещаем выбор даты
    ),
    html.Label('Дата конца:'),
    dcc.DatePickerSingle(
        id='date-end',
        display_format='YYYY-MM-DD',
        date=date_end_default.strftime('%Y-%m-%d'),  # Преобразование в строку
        disabled=True  # Запрещаем выбор даты
    ),
    dcc.Graph(id='object-count-graph'),
])


@app.callback(
    Output('object-count-graph', 'figure'),
    Input('date-start', 'date'),
    Input('date-end', 'date')
)
def update_graph(date_start, date_end):
    # преобразовывавают строки в формат даты
    date_start = datetime.strptime(date_start, '%Y-%m-%d')
    date_end = datetime.strptime(date_end, '%Y-%m-%d')


    with SSHTunnelForwarder(
            (host, 22),
            ssh_password=secret,
            ssh_username=user,
            remote_bind_address=(db_host, db_port)
    ) as server:
        conn = psycopg2.connect(
            host=db_host,
            port=server.local_bind_port,
            user=db_username,
            password=db_password,
            database=db_database
        )
        data = get_data(conn, date_start, date_end)

    df = pd.DataFrame(data) #cоздается объект DataFrame

    fig = {
        'data': [dict(x=df['time_interval'], y=df['object_count'], type='bar')], #по х-интервал по у количество, bar-гистограмма

        'layout': dict(title='Количество созданных объектов по времени')
    }

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
