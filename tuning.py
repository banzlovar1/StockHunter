import pandas as pd
#from test_wrapper import test_wrapper
from account import Account
from copy import deepcopy
import os
import numpy as np
import multiprocessing as mp
import time 
import copy

class Tuning():
    def __init__(self) -> None:
        pass

    def tune(self, model, data, tickers, min_params, max_params):
        best_param = (0,0,0)
        results = {}
        params = []
        # test on lower and start climbing
        print('Tuning begin')
        for i in np.arange(min_params[0], max_params[0], .01):
            for j in np.arange(min_params[1], max_params[1], .1):
                params.append((round(i,3), round(j,3)))
                # user = Account('tuner', 'tuner@gmail.com', 1000, 1000, 1000)
                # model(data, tickers, user, stop_loss=round(i,3), momentum_drop=round(j,3))
                # results[(round(i,3),round(j,3))] =  user.get_value()
                # del user
        with mp.Pool(8) as pool:
            # start_time = time.perf_counter()
            processes = [pool.apply_async(model, args=(data, tickers, Account('tuner', 'tuner@gmail.com', 1000, 1000, 1000), x[0], x[1])) for x in params]
            result = [p.get() for p in processes]
            # finish_time = time.perf_counter()
            # print(f"Program finished in {finish_time-start_time} seconds")
        # print(result)
        sorted_results = sorted(result, reverse=True)
        return sorted_results[0][1], sorted_results[0][2]