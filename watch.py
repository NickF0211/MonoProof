


class Watch():

    watch = None

    def __init__(self, lit_num):
        self.watch_list = [None] * (lit_num+1)
        Watch.watch = self

    def add_watch(self, lit, clause):
        if lit < 0:
            lit = -lit

        if self.watch_list[lit] is None:
            self.watch_list[lit] = set()

        self.watch_list[lit].add(clause)

    def remove_watch(self, lit, clause):
        index = abs(lit)
        assert (not self.watch_list[index] is None)
        self.watch_list[index].remove(clause)

    def notify_change(self, lit):
        if lit >= 0:
            index = lit
        else:
            index = -lit
        if not self.watch_list[index] is None:
            for clause in self.watch_list[index].copy():
                if not clause.notify_change(lit):
                    return False

        return True