import yfinance as yf
import argparse
from datetime import date, datetime
from enum import IntEnum
import os
import time

YYYY_MM_DD_FORMAT = '%Y-%m-%d'
YYYYMMDD_FORMAT = '%Y%m%d'


SCRIPT_DESCRIPTION = '''
Download Yahoo Finance historical data for Equity (common-stocks/ETFs)
It supports running against multiple tickers for a given as-of date (run date)
and stores each ticker in a <ticker>-<as-of-date>-<epoch-millis>.csv format
at a storage area.

In general, ETF and common stock tickers can be stored at the same location. 
If one ticker is generated multiple times on the same day, newer runs would 
have a newer <epoch-millis> timestamp
'''


# return code
class ReturnCode(IntEnum):
    SUCCESS = 0
    NO_TICKER_TO_PROCESS = 1
    NON_EXISTING_TICKER_FILE = 2
    NON_EXISTING_OUTPUT_PATH = 3
    FAILED_TO_READ_FROM_TICKER_FILE = 4
    FAILED_TO_SAVE_TO_OUTPUT_PATH = 5
    FAILED_TO_FETCH_DATA_FROM_YAHOO = 6


def from_YYYY_MM_DD(ds: str) -> date:
    try:
        return datetime.strptime(ds, YYYY_MM_DD_FORMAT).date()
    except:
        raise ValueError(f'cannot convert {ds} by yyyy-mm-dd format')


def to_YYYY_MM_DD(dt: date) -> str:
    return datetime.strftime(dt, YYYY_MM_DD_FORMAT)


def to_YYYYMMDD(dt: date) -> str:
    return datetime.strftime(dt, YYYYMMDD_FORMAT)


def get_ticker_data(tickers: list[str], start_date: date, end_date: date):
    if not tickers:
        raise ValueError(f'{tickers} is not valid input for tickers')

    df = yf.download(
        tickers,
        start=to_YYYY_MM_DD(start_date),
        end=to_YYYY_MM_DD(end_date),
        auto_adjust=False, # keep Close and Adj. Close
    )
    return dict(
        (ticker, df.xs(ticker, level='Ticker', axis=1)) 
        for ticker in df.columns.levels[1]
    )


def read_tickers_from_file(ticker_file_path: str) -> list[str]:
    '''
    For example, the following content would yield SPY/VOO/GLD in the list 

    # file content
    SPY # S&P500 ETF

    VOO # S&P500 ETF
    # IWW 
    GLD

    :param ticker_file_path: Description
    :type ticker_file_path: str
    :return: Description
    :rtype: list[str]
    '''
    with open(ticker_file_path, 'r') as f:
        valid_list = []
        for line in f: 
            token = line.split('#')[0].strip()
            if token:
                valid_list.append(token)
    return valid_list


def save_to_csv_files(output_path: str, as_of_date: str, ticker: str, df, timestamp: int):
    file_path = os.path.join(output_path, f'{ticker}-{as_of_date}-{timestamp}.csv')
    print(f'writing data for {ticker} to {file_path}')
    df.to_csv(file_path)


def get_cli_parser():
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    parser.add_argument(
        "--start-date", 
        type=from_YYYY_MM_DD,
        required=True,
        help='start date in yyyy-mm-dd format',
    )
    parser.add_argument(
        '--end-date',
        type=from_YYYY_MM_DD,
        required=True,
        help='end date in yyyy-mm-dd format',
    )
    parser.add_argument(
        '--output-path',
        required=True,
        help='output file storage path, each ticker in <as-of-date>/<ticker>-<as-of-date>-<epoch-millis>.csv'
    )
    parser.add_argument(
        '--as-of-date',
        type=from_YYYY_MM_DD,
        required=True,
        help='as-of-date of the script running date (i.e. date of today)',
    )

    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        '--ticker',
        action='append',
        help='ticker to fetch data (use multiple times for multiple tickers)'
    )
    ticker_group.add_argument(
        '--ticker-file-path',
        help='a path to a file with all the tickers to fetch data'
    )
    return parser


def run() -> ReturnCode:
    parser = get_cli_parser()
    args = parser.parse_args()
    
    print(args)

    if not os.path.exists(args.output_path):
        return ReturnCode.NON_EXISTING_OUTPUT_PATH

    if args.ticker:
        tickers_to_fetch = list(args.ticker)
    elif args.ticker_file_path:
        if not os.path.exists(args.ticker_file_path):
            return ReturnCode.NON_EXISTING_TICKER_FILE
        try:
            tickers_to_fetch = read_tickers_from_file(args.ticker_file_path)
        except:
            return ReturnCode.FAILED_TO_READ_FROM_TICKER_FILE

    if not tickers_to_fetch:
        return ReturnCode.NO_TICKER_TO_PROCESS

    try:
        ret = get_ticker_data(tickers_to_fetch, args.start_date, args.end_date)
    except Exception as e:
        return ReturnCode.FAILED_TO_FETCH_DATA_FROM_YAHOO
    
    if not ret:
        return ReturnCode.FAILED_TO_FETCH_DATA_FROM_YAHOO
     
    as_of_date = to_YYYYMMDD(args.as_of_date)
    print(f'as-of-date is {as_of_date}')
    
    as_of_date_output_path = os.path.join(args.output_path, as_of_date)
    # make sure the ticker subdirectory exists
    os.makedirs(as_of_date_output_path, exist_ok=True)

    timestamp = time.time()
    for ticker, df in ret.items():
        # output_path is already validated
        save_to_csv_files(as_of_date_output_path, as_of_date, ticker, df, timestamp)

    return ReturnCode.SUCCESS


def main() -> int:
    rc: ReturnCode = run()
    # match rc:
    #     case ReturnCode.SUCCESS:
    print(f'rc: {rc.name}')
    return rc


if __name__ == '__main__':
    raise SystemExit(main())