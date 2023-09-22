import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import psycopg2
import pandas as pd
from sshtunnel import SSHTunnelForwarder


host = '185.20.224.243'
user = 'root'
secret = 'Js3vyA-3~4MA'
port = 22


db_host = 'localhost'
db_port = 5432
db_username = 'testuser'
db_password = 'TEST_PAROL'
db_database = 'er_bot_development'


def get_data(connection):
    curs = connection.cursor()
    curs.execute(
        """
        SELECT
         EXTRACT(YEAR FROM created_at) AS year,
         EXTRACT(MONTH FROM created_at) AS month,
        COUNT(*) AS user_count
        FROM users
        GROUP BY
        year, month
        ORDER BY
        year, month;
        """
    )
    data = curs.fetchall()
    return data


app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='user-count-2022'),
    dcc.Graph(id='user-count-2023'),


    dcc.Input(id='dummy-input-1', type='hidden', value=''),
    dcc.Input(id='dummy-input-2', type='hidden', value='')
])


@app.callback(
    Output('user-count-2022', 'figure'),
    Output('user-count-2023', 'figure'),
    [Input('dummy-input-1', 'value'),
     Input('dummy-input-2', 'value')]
)
def update_graph(dummy_value_1, dummy_value_2):

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
        data = get_data(conn)


    df = pd.DataFrame(data, columns=['year', 'month', 'users_count'])
    df_2022 = df[df['year'] == 2022]
    df_2023 = df[df['year'] == 2023]


    fig_2022 = {
        'data': [dict(x=df_2022['month'], y=df_2022['users_count'], type='bar', name='2022')],
        'layout': dict(title='Количество пользователей по месяцам в 2022 году')
    }

    fig_2023 = {
        'data': [dict(x=df_2023['month'], y=df_2023['users_count'], type='bar', name='2023')],
        'layout': dict(title='Количество пользователей по месяцам в 2023 году')
    }

    return fig_2022, fig_2023


if __name__ == '__main__':
    app.run_server(debug=True)

