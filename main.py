import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import ycnbc

# Initialize the Dash app
app = dash.Dash(__name__)

# Create an instance of the Markets class
markets_instance = ycnbc.Markets()

# Function to fetch bond data
def fetch_bond_data():
    try:
        bonds_data = markets_instance.bonds()
        return bonds_data
    except Exception as e:
        print(f"Error fetching bond data: {e}")
        return None

# Function to prepare yield curve data
def prepare_yield_curve(bonds_data):
    if bonds_data is None:
        return [], [], 0

    maturities = []
    yields = []
    yield_dict = {}

    for bond in bonds_data:
        if bond['symbol'].startswith('US'):
            maturities.append(bond['symbol'])
            yield_value = float(bond['last'].replace('%', '').strip())
            yields.append(yield_value)
            yield_dict[bond['symbol']] = yield_value

    slope = yield_dict.get('US10Y', 0) - yield_dict.get('US2Y', 0)
    return maturities, yields, slope

# Function to fetch futures data
def fetch_futures_data():
    try:
        futures_and_commodities_data = markets_instance.futures_and_commodities()
        data = [
            {
                "symbol": item.get('symbol', 'N/A'),
                "name": item.get('name', 'N/A'),
                "last_price": item.get('last', 'N/A'),
                "change": item.get('change', 'N/A'),
                "change_pct": item.get('change_pct', 'N/A'),
                "expiration_date": item.get('expiration_date', 'N/A'),
                "is_halted": item.get('EventData', {}).get('is_halted', 'N/A')
            }
            for item in futures_and_commodities_data
        ]
        return data
    except Exception as e:
        print(f"Error fetching futures data: {e}")
        return []

# Function to fetch currency data
def fetch_currency_data():
    try:
        currencies_data = markets_instance.currencies()
        currency_dict = {
            'EUR/USD': None,
            'USD/JPY': None,
            'GBP/USD': None,
            'USD/CAD': None,
            'USD/CHF': None,
            'AUD/USD': None,
        }

        for currency in currencies_data:
            if currency['symbol'] == 'EUR=':  # EUR/USD
                currency_dict['EUR/USD'] = currency
            elif currency['symbol'] == 'JPY=':  # USD/JPY
                currency_dict['USD/JPY'] = currency
            elif currency['symbol'] == 'GBP=':  # GBP/USD
                currency_dict['GBP/USD'] = currency
            elif currency['symbol'] == 'CAD=':  # USD/CAD
                currency_dict['USD/CAD'] = currency
            elif currency['symbol'] == 'CHF=':  # USD/CHF
                currency_dict['USD/CHF'] = currency
            elif currency['symbol'] == 'AUD=':  # AUD/USD
                currency_dict['AUD/USD'] = currency

        return currency_dict
    except Exception as e:
        print(f"Error fetching currency data: {e}")
        return None

# Dashboard layout
app.layout = html.Div(style={
    'backgroundColor': '#D3D3D3',
    'padding': '20px',
    'fontFamily': 'Arial, sans-serif',
    'overflow': 'auto'
}, children=[
    html.H1("Daily Economics", style={'textAlign': 'center', 'color': '#333'}),
    html.H2("Weekly Updates on Macro-Economic Topics", style={'textAlign': 'center', 'color': '#333', 'font-size': 24}),

    # Commentary section
    html.Div(children=[
        html.H2("Market Commentary", style={'textAlign': 'center', 'color': '#555'}),
        html.Div(children=[
            html.P(
                "The once-robust momentum of the 'Trump trade' has noticeably decelerated this week as market conditions cool. "
                "Treasury yield curves have already begun to price in the potential economic repercussions of a tariff regime "
                "proposed by the Trump administration, signaling investor caution. Concurrently, the Japanese yen has seen a "
                "significant appreciation, spurred by a surprising GDP expansion after two years of stagnation in industrial production—a "
                "development that suggests a potential shift in Japan’s economic trajectory."
            ),
            html.P(
                "On the commodities front, markets are in retreat, reflecting diminished investor appetite. This decline aligns with a broader "
                "transformation of consumer sentiment, which some are calling the rise of Trump’s 'Bitcoin Economy.' This paradigm reflects a growing "
                "shift toward digital assets and riskier speculative investments, as traditional economic indicators face heightened uncertainty."
            ),
            html.P(
                "Adding to the complexity, CPI figures have shown further deterioration, highlighting persistent inflationary pressures. Despite this, "
                "the Federal Reserve remains steadfast, expressing confidence in its ability to interpret economic data and adjust monetary policy accordingly. "
                "Market expectations point to a measured pace of rate cuts in the near future, as the Fed looks to balance inflation management with broader "
                "economic stability."
            ),
            html.P(
                "Consumer sentiment, however, continues to struggle under the weight of high inflation and elevated interest rates, exacerbated by lingering "
                "aftershocks of the COVID-19 pandemic. Despite these challenges, the current economic environment offers glimmers of stability. Labor markets "
                "remain resilient, and corporate earnings have not yet shown broad signs of capitulation, suggesting that the economy is navigating a period of cautious optimism."
            )
        ], style={
            'border': '1px solid #ccc',
            'borderRadius': '5px',
            'backgroundColor': '#ffffff',
            'padding': '15px',
            'margin': '10px',
            'boxShadow': '0 2px 4px rgba(0, 0, 0, 0.1)'
        })
    ]),

    # Treasury yield curve section
    html.Div(children=[
        html.H2('Treasury Yield Curve', style={'textAlign': 'center'}),
        dcc.Graph(id='yield-curve'),
        html.Div(id='slope-description', style={'fontSize': '18px', 'textAlign': 'center', 'marginTop': '10px'}),
        html.Div('This represents the difference between the 2-year and 10-year U.S. Treasury yields.',
                 style={'fontSize': '12px', 'color': 'gray', 'textAlign': 'center'})
    ]),

    # Currency dashboard section
    html.Div(children=[
        html.H2("Current Currency Prices", style={'textAlign': 'center', 'color': '#555'}),
        html.Div(id='currency-data', style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap',
                                            'textAlign': 'center'}),
    ]),

    # Dot Plot
    dcc.Graph(id='currency-dot-plot', style={'height': '60vh'}),

    # Futures and commodities data section
    html.Div(children=[
        html.H2("Futures and Commodities Data", style={'textAlign': 'center'}),
        dash_table.DataTable(
            id='live-data-table',
            columns=[
                {"name": "Symbol", "id": "symbol"},
                {"name": "Name", "id": "name"},
                {"name": "Last Price", "id": "last_price"},
                {"name": "Change", "id": "change"},
                {"name": "Change Percentage", "id": "change_pct"},
                {"name": "Expiration Date", "id": "expiration_date"},
                {"name": "Is Halted", "id": "is_halted"}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px', 'border': '1px solid #ddd'},
            style_header={'backgroundColor': 'lightblue', 'fontWeight': 'bold', 'color': '#333'},
            page_size=10
        )
    ]),

    # Interval component
    dcc.Interval(id='interval-component', interval=30 * 1000, n_intervals=0),

    # Disclaimer
    html.Div('Data sourced from CNBC. This dashboard is for educational and informational purposes only.',
             style={'textAlign': 'center', 'marginTop': '20px', 'fontSize': '12px', 'color': 'gray'})
])

# Callbacks (unchanged from previous sections)

@app.callback(
    [Output('yield-curve', 'figure'),
     Output('slope-description', 'children')],
    Input('interval-component', 'n_intervals')
)
def update_yield_curve(n_intervals):
    bonds_data = fetch_bond_data()
    maturities, yields, slope = prepare_yield_curve(bonds_data)

    figure = {
        'data': [go.Scatter(x=maturities, y=yields, mode='lines+markers', name='Yield Curve')],
        'layout': go.Layout(title='U.S. Treasury Yield Curve', xaxis={'title': 'Maturity'}, yaxis={'title': 'Yield (%)'})
    }

    curve_state = "Flattening" if slope < 0 else "Steepening"
    color = "red" if slope < 0 else "green"

    slope_text = html.Div([
        html.Span(f'2/10 Year Slope: {slope:.2f}', style={'color': color, 'fontWeight': 'bold'}),
        html.Span(f' - {curve_state}', style={'fontWeight': 'bold'})
    ])

    return figure, slope_text

@app.callback(
    [Output('currency-data', 'children'),
     Output('currency-dot-plot', 'figure')],
    Input('interval-component', 'n_intervals')
)
def update_currency_data(n_intervals):
    currency_data = fetch_currency_data()
    if currency_data:
        currency_display = []
        currency_records = []

        for symbol, data in currency_data.items():
            if data is None or data.get('last') is None or data.get('open') is None:
                continue

            try:
                last_price = float(data['last'])
                open_price = float(data['open'])
                color = 'green' if last_price > open_price else 'red'
            except ValueError:
                last_price = "N/A"
                open_price = "N/A"
                color = 'gray'

            currency_display.append(
                html.Div(
                    f'{symbol}: {last_price} (Open: {open_price})',
                    style={
                        'padding': '10px',
                        'margin': '5px',
                        'border': '1px solid #ccc',
                        'borderRadius': '5px',
                        'backgroundColor': color,
                        'color': 'white',
                        'width': '150px',
                        'textAlign': 'center'
                    }
                )
            )

            currency_records.append({'Currency Pair': symbol, 'Price': last_price})

        df = pd.DataFrame(currency_records)
        fig = px.scatter(df, x='Currency Pair', y='Price', size=[50] * len(df), color='Currency Pair',
                         title='Current Prices of Currency Pairs')

        return currency_display, fig

    return "Unable to fetch currency data.", go.Figure()

@app.callback(
    Output('live-data-table', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_live_data(n_intervals):
    return fetch_futures_data()

if __name__ == '__main__':
    app.run_server(debug=True, port=5006)
