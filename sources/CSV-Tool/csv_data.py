import random
import rstr
import re


class CSV_Data():
    def __init__(self, data: list=None, pb_tick=lambda: None, show=lambda: None):
        self.data = data
        self.pb_tick = pb_tick
        self.show = show


    def __len__(self):
        return len(self.data)


    def __getitem__(self, i):
        if self.data is None:
            return None
        return self.data[i]


    def set(self, data):
        self.data=data

    
    def isEmpty(self):
        return self.data is None or len(self.data) == 0


    def swap_columns(self, a_index, b_index):
        if self.isEmpty():
            return
        
        num_cols = len(self.data[0])
        if a_index >= num_cols or b_index >= num_cols or a_index < 0 or b_index < 0:
            raise IndexError("Column index out of range")
        
        for i in range(len(self.data)):
            self.pb_tick()
            self.data[i][a_index], self.data[i][b_index] = self.data[i][b_index], self.data[i][a_index]


    def sort_column(self, col, descending):
        def convert_value(val):
            try:
                return int(val)
            except ValueError:
                try:
                    return float(val)
                except ValueError:
                    if val == "":
                        return 0
                    else:
                        return val
        if self.isEmpty():
            return
        tmp_data = [(convert_value(self.data[i][col]), i) for i in range(1, len(self.data)-1)]
        tmp_data.sort(reverse=descending)
        self.data = [self.data[0]] + [self.data[ln[1]] for ln in tmp_data]
        self.show()


    def delete_column(self, col):
        if self.isEmpty():
            return
        for i, line in enumerate(self.data):
            self.pb_tick()
            del line[col]
        self.show()


    def shuffle_column(self, col):
        if self.isEmpty():
            return
        tmp = [self.data[i][col] for i in range(1,len(self.data)-1)]
        random.shuffle(tmp)

        for i in range(1,len(self.data)-1):
            self.pb_tick()
            self.data[i][col] = tmp[i-1]
        self.show()


    def randomize_regex(self, index, regex):
        if self.isEmpty():
            return
        for i, line in enumerate(self.data[1:]):
            self.pb_tick()
            line[index] = rstr.xeger(regex)


    def randomize_float(self, index, min, max, dpoint):
        if self.isEmpty():
            return
        for i, line in enumerate(self.data[1:]):
            self.pb_tick()
            line[index] = str(round(random.uniform(min, max), dpoint))


    def randomize_int(self, index, min, max):
        if self.isEmpty():
            return
        for i, line in enumerate(self.data[1:]):
            self.pb_tick()
            line[index] = str(random.randint(min, max))

    
    def remove_duplicates(self):
        if self.isEmpty():
            return
        seen = set()
        unique = []
        for line in self.data:
            self.pb_tick()
            tup = tuple(line)
            if tup not in seen:
                seen.add(tup)
                unique.append(line)
        self.data = unique

 
    def export_columns(self,cols: list):
        if self.isEmpty():
            return
        out = []
        for line in self.data:
            self.pb_tick()
            out.append([line[i] for i in cols])
        self.show()
        return out
    

    def search(self,regex: str):
        if self.isEmpty():
            return
        out = [self.data[0]]
        for line in self.data:
            self.pb_tick()
            found = False
            for val in line:
                if not re.search(regex, val) is None:
                    found=True
            if found:
                out.append(line)
        self.show()
        return out
    

    def delete_lines(self,lines_index: list):
        if self.isEmpty():
            return
        lines_index.sort(reverse=True)
        for i in lines_index:
            del self.data[i]
        self.show()
