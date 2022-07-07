import pandas as pd


class Grid:
    def __init__(self, startpoint: float, interval: float, size: int = 10) -> None:
        self.grid_series = pd.Series()
        self.current_pointer = 0
        self.startpoint = startpoint
        self.interval = interval
        self.size = size
        self.generate_grid_series()

    def generate_grid_series(self) -> pd.Series:
        grid_list_left = []
        grid_list_right = []
        next_left_value = self.startpoint
        next_right_value = self.startpoint
        for x in range(0, self.size):
            next_left_value = next_left_value*(1-self.interval)
            next_right_value = next_right_value*(1+self.interval)
            grid_list_left.append(next_left_value)
            grid_list_right.append(next_right_value)

        grid_list_left.append(self.startpoint)
        grid_list_left.extend(grid_list_right)
        grid_list_left.sort()
        result_series = pd.Series(grid_list_left)
        index_list = result_series.index.to_list()
        result_series.index = [i-self.size for i in index_list]
        self.grid_series = result_series
        return result_series
