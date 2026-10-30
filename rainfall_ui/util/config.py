# Code for parsing command-line arguments


import argparse


def parse_args():
    ''' Function to parse command-line arguments '''
    parser = argparse.ArgumentParser(
        prog='Rainfall unevenness analysis',
        description='Basic configuration for rainfall unevenness analysis'
    )
    parser.add_argument('-s', '--start_yr', metavar='START_YEAR', help='Enter the start year', type=int, default=1980)
    parser.add_argument('-e', '--end_yr', metavar='END_YEAR', help='Enter the end year', type=int, default=2020)
    parser.add_argument('-t', '--th_yr', metavar='TH_YEAR', help='Enter the threshold year', type=int, default=30)
    parser.add_argument('-o', '--overwrite', metavar='OVERWRITE', help='Whether overwrite existing files, 0 (False) or 1 (True)', type=int, default=0)
    args = parser.parse_args()

    return args

